import psycopg
from typing import Literal
import os
from schemas import DB_Schema, DB_User_Schema
from psycopg.types.json import Jsonb
from datetime import datetime, timezone

def load_db_config() -> str:
    db_url = os.getenv("DB_URL", None)
    if db_url is not None:
        return db_url
    else:
        db_user = os.getenv("DB_USER", "project4_app")
        db_password = os.getenv("DB_PASSWORD", "project4_minimal")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "project4_minimal")
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


async def db_insert(conn: psycopg.Connection, entry: DB_Schema):
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO app.tasks (
            username, request_id, request_host, request_port, task_id, status, 
            input_payload, output_payload, error, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                entry.username,
                entry.request_id,
                entry.request_host,
                entry.request_port,
                entry.task_id, 
                entry.status, 
                Jsonb(entry.input_payload), 
                Jsonb(entry.output_payload),
                entry.error,
                entry.created_at,
                entry.updated_at,
            )
        )

def db_update_status(conn: psycopg.Connection, task_id: str, status: Literal["queued", "running", "succeeded", "failed"]):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.tasks
            SET status = %s
            WHERE task_id = %s
            """,
            (status, task_id)
        )
        cur.execute(
            """
            UPDATE app.tasks
            SET updated_at = %s
            WHERE task_id = %s
            """,
            (datetime.now(timezone.utc), task_id)
        )


def db_update_output_payload(conn: psycopg.Connection, task_id: str, payload: dict):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.tasks
            SET output_payload = %s
            WHERE task_id = %s
            """,
            (Jsonb(payload), task_id)
        )
        cur.execute(
            """
            UPDATE app.tasks
            SET updated_at = %s
            WHERE task_id = %s
            """,
            (datetime.now(timezone.utc), task_id)
        )

def db_update_error(conn: psycopg.Connection, task_id: str, error: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.tasks
            SET error = %s
            WHERE task_id = %s
            """,
            (error, task_id)
        )
        cur.execute(
            """
            UPDATE app.tasks
            SET updated_at = %s
            WHERE task_id = %s
            """,
            (datetime.now(timezone.utc), task_id)
        )

async def db_select_request(conn: psycopg.Connection, request_id: str):
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT 
            username,
            request_id,
            request_host,
            request_port,
            task_id,
            status,
            input_payload,
            output_payload,
            error, 
            created_at,
            updated_at
            FROM app.tasks
            WHERE request_id = %s;
            """,
            (request_id,)
        )
        rows = await cur.fetchall()
        return rows if len(rows)!=0 else None
    
async def db_select_task(conn: psycopg.Connection, task_id: str):
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT 
            username,
            request_id,
            request_host,
            request_port,
            task_id,
            status,
            input_payload,
            output_payload,
            error, 
            created_at,
            updated_at
            FROM app.tasks
            WHERE task_id = %s;
            """,
            (task_id,)
        )
        return await cur.fetchone()
    
async def db_get_user(conn: psycopg.Connection, name: str):
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT 
            name,
            password,
            role
            FROM app.users
            WHERE name = %s;
            """,
            (name,)
        )
        return await cur.fetchone()
    


async def db_create_user(conn: psycopg.Connection, entry: DB_User_Schema):
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO app.users (name, password, role)
            VALUES (%s, %s, %s)
            """,
            (
                entry.name,
                entry.password,
                entry.role,
            )
        )