from fastapi import FastAPI, middleware, Request, HTTPException, Depends, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from db import db_insert, db_select_request, db_select_task, load_db_config, db_create_user, db_get_user
from schemas import Sleep_In, DB_Schema, User_In, LLM_In
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
import uuid, time, asyncio
from celery_app import celery_app
import tasks
from tasks import llm_run
import anyio, os
from celery.result import AsyncResult
from datetime import datetime, timezone
from auth import auth_sign_jwt, auth_decode_username
from typing import Optional, Any, Dict
from llm import MyLLM

bearer = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_dsn = load_db_config()
    pool = AsyncConnectionPool(conninfo=db_dsn, min_size=1, max_size=5, open=False)
    await pool.open()
    app.state.db_pool = pool
    app.state.llm = llm
    try:
        yield
    finally:
        await app.state.db_pool.close()

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def add_request_id(request:Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = rid
    start = time.time()
    resp = await call_next(request)
    cost = time.time() - start
    resp.headers["x-request-id"] = rid
    resp.headers["x-cost-seconds"] = f"{cost:04}"
    return resp

@app.post("/login")
async def login(payload: User_In):
    pool = app.state.db_pool
    async with pool.connection() as conn:
        user = await db_get_user(conn=conn, name=payload.name)
    if user is None or payload.password!=user[1]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    return {
        "access_token": auth_sign_jwt(payload.name),
        "token_type": "bearer"
    }

async def authenticate(creds: Optional[HTTPAuthorizationCredentials] = Security(bearer)):
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authoriazation headre"
        )
    token = creds.credentials
    scheme = creds.scheme
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Use: Authorization: Bearer <token>")
    
    user_name = auth_decode_username(token=token)
    pool = app.state.db_pool
    async with pool.connection() as conn:
        user_info = await db_get_user(conn=conn, name=user_name)
    if user_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unregistered username"
        )
    return {
        "name": user_info[0],
        "role": user_info[2]
    }

async def require_admin(user: Dict[str, Any] = Depends(authenticate)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user

@app.post("/sleep")
async def sleep(request: Request, sleep_in: Sleep_In, user: Dict[str, Any] = Depends(authenticate)):
    n = sleep_in.n
    sec = sleep_in.sec
    start = time.time()
    results = await asyncio.gather(*[_enque_sleep(request, sec, user) for _ in range(n)])
    cost = time.time() - start
    return {
        "n": n,
        "request_id": request.state.request_id,
        "enque_n_seconds": cost,
        "results": results,
    }

@app.post("/llm")
async def llm(request: Request, llm_in: LLM_In, user: Dict[str, Any] = Depends(authenticate)):
    input_text = llm_in.input_text
    tid = str(uuid.uuid4())
    start = time.time()
    r = await anyio.to_thread.run_sync(lambda: llm_run.delay(task_id=tid, input_text=input_text))
    cost = time.time() - start
    entry = DB_Schema(
        username=user.get("name"),
        request_id=request.state.request_id,
        request_host=request.client.host,
        request_port=str(request.client.port),
        task_id=tid,
        status="queued",
        input_payload={"task": "llm", "input_text": input_text},
        output_payload=None,
        error=None,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )
    pool = app.state.db_pool
    async with pool.connection() as conn:
        await db_insert(conn=conn, entry=entry)
    return {
        "username": user.get("name"),
        "enque_seconds": cost,
        "task": "llm",
        "task_id": tid,
        "celery_id": r.id,
    }

async def _enque_sleep(request: Request, sec:float,  user: Dict[str, Any]):
    start = time.time()
    tid = str(uuid.uuid4())
    r = await anyio.to_thread.run_sync(lambda: tasks.sleep.delay(tid, sec))
    cost = time.time() - start
    pool = app.state.db_pool
    entry = DB_Schema(
        username=user.get("name"),
        request_id=request.state.request_id,
        request_host=request.client.host,
        request_port=str(request.client.port),
        task_id=tid,
        status="queued",
        input_payload={"task": "sleep", "sec": sec},
        output_payload=None,
        error=None,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )
    async with pool.connection() as conn:
        await db_insert(conn=conn, entry=entry)

    return {
        "username": user.get("name"),
        "enque_seconds": cost,
        "task": "sleep",
        "task_id": tid,
        "celery_id": r.id,
    }

@app.get("/task/{task_id}")
async def task_status(task_id: str, user = Depends(authenticate)):
    return await _read(task_id, user)

@app.get("/request/{request_id}")
async def request_status(request_id: str, user = Depends(authenticate)):
    pool = app.state.db_pool
    start = time.time()
    async with pool.connection() as conn:
        rows = await db_select_request(conn, request_id)
    cost = time.time() - start
    if rows is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    for row in rows:
        if row[0] != user.get("name"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized access"
            )
    return {
        "username": user.get("name"),
        "request_id": rows[0][1],
        "count": len(rows),
        "extract_seconds": cost,
        "results": [{"task_id": row[4], "status": row[5], "output": row[7]} for row in rows] 
    }

async def _read(task_id: str, user: Dict[str, Any]):
    pool = app.state.db_pool
    start = time.time()
    async with pool.connection() as conn:
        row = await db_select_task(conn=conn, task_id=task_id)
    cost = time.time() - start
    if row is None: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if row[0] != user.get("name"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access"
        )
    return {
        "username": user.get("name"),
        "task_id": task_id,
        "status": row[5],
        "extract_seconds": cost,
        "output": row[7],
    }