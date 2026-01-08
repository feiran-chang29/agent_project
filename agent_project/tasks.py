from __future__ import annotations
from celery_app import celery_app
import time
from db import db_update_status, db_update_error, db_update_output_payload, load_db_config
from schemas import DB_Schema
from psycopg_pool import ConnectionPool
from celery.signals import worker_process_shutdown
from llm import MyLLM
import traceback


_pool = None

def get_pool():
    db_dsn = load_db_config()
    global _pool
    if _pool is None:
        _pool = ConnectionPool(conninfo=db_dsn, min_size=1, max_size=5)
    return _pool

@worker_process_shutdown.connect
def close_pool(**kwargs):
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None

def update_database(task: callable):
    def wrapper(*args, **kwargs):
        if "task_id" in kwargs:
            task_id = kwargs.get("task_id")
        else:
            task_id = args[0]

        status = 'running'
        result = None
        cost = -1.0
        output = None
        error = None

        pool = get_pool()
        with pool.connection() as conn:
            db_update_status(conn=conn, task_id=task_id, status=status)
        start = time.time()
        try:
            output = task(*args, **kwargs)
            status = 'succeeded'
        except Exception as e:
            status = 'failed'
            error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        finally:
            cost = time.time() - start
            result = {"task": task.__name__, "status": status, "cost_seconds": cost, "output": output}
        with pool.connection() as conn:
            db_update_status(conn=conn, task_id=task_id, status=status)
            db_update_output_payload(conn=conn, task_id=task_id, payload=result)
            if error is not None:
                db_update_error(conn=conn, task_id=task_id, error=error)
        return result
    return wrapper

@celery_app.task
@update_database
def sleep(task_id: str, sec: float):
    time.sleep(sec) 
    return {"sec": sec}

@celery_app.task
@update_database
def llm_run(task_id: str, input_text: str):
    llm = MyLLM()
    messages = [{"role": "system", "content": "你是一个有用的AI助手。"}]
    messages.append({"role": "user", "content": input_text})
    response = llm.invoke(messages=messages)
    return {"response": response}

