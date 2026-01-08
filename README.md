# Asynchronous LLM Inference & Document Processing Platform

A lightweight asynchronous backend for document summarization and structured information extraction using a local LLM (e.g., a 7B model). The system exposes an HTTP API (FastAPI) for job submission and status queries, executes long-running inference asynchronously via Celery workers (Redis), and persists task state and artifacts in PostgreSQL for traceability.

This repository focuses on an engineering-first pipeline: durable task tracking, structured outputs (JSON) validated by Pydantic, and failure handling with repair/retry.

---

## What it does

- Accepts document text (or extracted text) as input and runs **local LLM inference** for:
  - summarization
  - structured information extraction (JSON)
- Executes inference asynchronously:
  - API returns quickly with a task identifier
  - background worker performs inference and persists results
- Persists task lifecycle data and artifacts to PostgreSQL for reproducible runs.

---

## Engineering highlights

- **Async job architecture**: FastAPI (async/await) + Celery workers for non-blocking request handling.
- **Durable state**: PostgreSQL-backed task status tracking (not only in-memory).
- **Structured output hardening**: Pydantic schema validation for JSON extraction; repair-on-failure retries to improve robustness.
- **Security**: JWT authentication with per-user authorization for task access.
- **Containerized services**: Docker Compose wiring for API/worker + Redis + Postgres.

---

## Tech stack

- Python, FastAPI, Pydantic
- Celery, Redis
- PostgreSQL
- Docker / Docker Compose
- JWT authentication

---

## Code map (current)

- `agent_project/main.py` — FastAPI app entry and HTTP routes
- `agent_project/auth.py` — JWT auth helpers and authorization logic
- `agent_project/schemas.py` — Pydantic request/response schemas
- `agent_project/db.py` — PostgreSQL access helpers (task persistence)
- `agent_project/celery_app.py` — Celery app configuration
- `agent_project/tasks.py` — Celery worker tasks (inference execution + status updates)
- `agent_project/llm.py` — Local LLM invocation wrapper

Infrastructure:
- `compose.yml` — local orchestration (Redis/Postgres and app services if configured)
- `DockerFile` — container build
- `requirements.txt` — dependencies

---

## Status

This project is under active development. The core pipeline (submit → async run → persist status/output) is implemented; reliability/ops hardening and full end-to-end verification across environments is ongoing.

---

## Next steps (planned)

- End-to-end verified Quickstart instructions
- Idempotency for task submission (Idempotency-Key)
- Explicit timeouts and retry/backoff policy tuning
- Structured logging and request/task correlation IDs
- Basic integration tests and CI

---

## Notes

This repository intentionally keeps setup instructions minimal until the deployment path is fully verified across machines and container environments.
