# BrightCore Recruitment — Step 01

Step 01 establishes the backend foundation: FastAPI, PostgreSQL, Redis, configuration, and health endpoints.

## Prerequisites
- Python 3.12+
- Docker Desktop / Docker Engine with Docker Compose
- Postman

## 1. Configure environment
Copy `.env.example` to `.env`.

PowerShell:
```powershell
Copy-Item .env.example .env
```

Linux/macOS:
```bash
cp .env.example .env
```

For local development, the sample credentials are development-only. Change them before deployment.

## 2. Start PostgreSQL and Redis
```bash
docker compose up -d postgres redis
docker compose ps
```

## 3. Create a Python environment
PowerShell:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux/macOS:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Run the API
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive API docs: http://127.0.0.1:8000/docs

## 5. Test with Postman
Import both:
- `postman/BrightCore_Step01_Health.postman_collection.json`
- `postman/BrightCore_Local.postman_environment.json`

Select the `BrightCore Local` environment and run the requests in order:
1. API Root
2. Liveness
3. Readiness

Expected responses:
- Root: HTTP 200
- Liveness: HTTP 200
- Readiness: HTTP 200 when PostgreSQL and Redis are reachable; otherwise HTTP 503

## Notes
- `/health/live` checks that the process is alive.
- `/health/ready` checks PostgreSQL and Redis connectivity.
- No business endpoints, authentication, or database migrations are added yet. Those belong to later steps.
- Do not commit `.env` or real secrets to Git.
