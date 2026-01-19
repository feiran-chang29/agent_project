from pydantic import BaseModel
from dataclasses import dataclass
from typing import Literal, Optional, Dict
from psycopg.types.json import Jsonb
from datetime import datetime

class DB_Schema(BaseModel):
    username: str
    request_id: str
    request_host: str
    request_port: str
    task_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    input_payload: Dict
    output_payload: Optional[Dict]
    error: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

class DB_User_Schema(BaseModel):
    name: str
    password: str
    role: Literal["user", "admin"]


class Sleep_In(BaseModel):
    n: int = 2
    sec: float = 3

class User_In(BaseModel):
    name: str
    password: str

class LLM_In(BaseModel):
    input_text: str