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
- No business endpoints or authentication are added yet. Those belong to later steps.
- Do not commit `.env` or real secrets to Git.

## Step 2: Create and apply the users migration

### 2.7: Configure Alembic

Alembic is already listed in `requirements.txt`:
```text
alembic>=1.13,<2.0
```

Install the project requirements:
```bash
pip install -r requirements.txt
```

Alembic is already initialized in this project. If setting up a fresh copy that does not have an `alembic` directory or `alembic.ini`, initialize it with:
```bash
alembic init alembic
```

In the existing `alembic.ini`, set the `sqlalchemy.url` fallback to:
```ini
sqlalchemy.url = postgresql+psycopg://brightcore:brightcore_dev_only@localhost:5432/brightcore
```

The migration environment reads the actual database URL from the application configuration, so this `alembic.ini` value is only a fallback.

Generate a migration from the SQLAlchemy models:
```bash
alembic revision --autogenerate -m "create users table"
```

Alembic creates a revision file in `alembic/versions/`. Open and review the generated migration before applying it. Verify that it creates the `users` table with a UUID primary key, a unique email constraint, the role check constraint, and the `created_at` and `updated_at` timestamps.

Autogeneration compares model metadata with the current database; it does not guarantee that every intended schema change is correct. Review and adjust the migration as needed.

Apply the reviewed migration:
```bash
alembic upgrade head
```

Check the current migration state and revision history:
```bash
alembic current
alembic history
```
