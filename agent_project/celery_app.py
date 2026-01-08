from celery import Celery
import os

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1/0")
BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://127.0.0.1/1")

celery_app = Celery(
    "project4_minimal",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=["tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
)