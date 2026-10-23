# BrightCore E-Recruitment

BrightCore Recruitment is a recruitment web application with a React frontend
and a FastAPI backend. The production Docker Compose setup runs the web app,
API, PostgreSQL database, and Redis.

This guide takes you from cloning the repository to starting the complete app
on your own computer. The final startup command is `auto_start.sh`.

Important: Do not skip any step in this guide. Follow the steps in order, and
make sure the administrator password is at least 12 characters long when you
are prompted during startup.

## Prerequisites

- Git
- Docker Desktop on Windows or Docker Engine with the Docker Compose plugin on
  Linux. Docker must be running.
- Python 3.12 or newer installed on your computer. The startup script uses it
  to run the test suite before starting the app.
- On Windows, Git for Windows (Git Bash) or WSL to run the Bash startup script.

The frontend and API run in Docker, so you don’t need to manually install dependencies to run the Local or production environment.

## 1. Clone the repository

Choose either HTTPS or SSH:

```bash
git clone https://github.com/shumbushojeanbaptiste/recruitment.brightCore.rw.git
cd recruitment.brightCore.rw
```

Or, if your GitHub SSH key is configured:

```bash
git clone git@github.com:shumbushojeanbaptiste/recruitment.brightCore.rw.git
cd recruitment.brightCore.rw
```

On Windows, run the clone commands in PowerShell, Git Bash, or a WSL terminal.

## 2. Create the production environment file

Copy the example configuration. The production Compose setup expects the file
to be named `.env.production`.

PowerShell:

```powershell
Copy-Item .env.production.example .env.production
```

Linux, macOS, Git Bash, or WSL:

```bash
cp .env.production.example .env.production
```

Generate two different secrets. Use the first output for
`POSTGRES_PASSWORD` and the second for `JWT_SECRET_KEY`.

PowerShell (run each command and copy its output):

```powershell
py -3.12 -c "import secrets; print(secrets.token_hex(32))"
py -3.12 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Linux, macOS, Git Bash, or WSL:

```bash
openssl rand -hex 32
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Edit `.env.production` and replace the placeholder values for
`POSTGRES_PASSWORD` and `JWT_SECRET_KEY` with the generated outputs. Keep
`POSTGRES_DB`, `POSTGRES_USER`, and the other example settings unless you have a
reason to change them.

PowerShell:

```powershell
notepad .env.production
```

Linux, macOS, Git Bash, or WSL:

```bash
${EDITOR:-nano} .env.production
```

Do not commit `.env.production`, share the secrets, or use these local
credentials for a public deployment. The file is excluded from Git.

## 3. Prepare Python for the startup script

The startup script runs `pytest` on your computer before building and starting
the containers. Create a virtual environment and install the Python
requirements so the test command is available. The tests use an isolated
SQLite database and a fake Redis client, and provide test-only settings during
startup, so no local `.env` file or running database/Redis services are needed.

PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux, macOS, Git Bash, or WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If Python 3.12 is not your default on Windows, use the `py -3.12` launcher as
shown. In a Linux or macOS environment, use a Python 3.12+ installation.

## 4. Start the application

The script must run in Bash, not directly as a PowerShell script. On Windows,
open Git Bash or WSL in the cloned repository. You can also run it from
PowerShell if Git Bash is installed and `bash` is available on `PATH`.

Git Bash or WSL on Windows:

```bash
bash ./auto_start.sh
```

Linux or macOS:

```bash
bash ./auto_start.sh
```

The script runs the tests, validates the production Compose configuration,
downloads required images, builds the API and frontend, starts PostgreSQL and
Redis, applies database migrations, starts the API and web app, and imports
the sample recruitment data. The initial image download and build can take
several minutes.

When prompted, enter the administrator's full name, email, and a password of
at least 12 characters (up to 128 characters) twice. Do not skip the setup
prompt, and make sure the password meets the minimum length requirement.
**There is no hard-coded seeded admin username or password.** These are the
credentials you create and will use to sign in. Running the script again with
the same admin email verifies the existing administrator rather than creating a
duplicate.

When startup finishes, open:

- Web app: [http://localhost/](http://localhost/)
- API documentation: [http://localhost/docs](http://localhost/docs)
- API readiness check: [http://localhost/health/ready](http://localhost/health/ready)

The readiness endpoint should return HTTP 200 when the API can reach its
database and Redis. If startup fails, review the error printed by the script
and the service logs:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs --tail 100
```

If port 80 is already in use, stop the application using that port and rerun
the startup script.

## Stop and restart

To stop the containers without deleting the database, Redis data, or uploaded
files:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

To start the existing containers again:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

The startup script can also be run again; it reruns tests and startup steps.
The sample SQL uses conflict handling for its job records.

## Technology choices

- **React, TypeScript, and Vite** provide a component-based frontend with
  compile-time type checking and a fast development/build workflow.
- **FastAPI and Python** provide the API, request validation, and generated
  interactive API documentation.
- **PostgreSQL** stores persistent application data, with **SQLAlchemy** for
  database access and **Alembic** for versioned schema migrations.
- **Redis** is included as the application’s supporting in-memory data
  service.
- **Docker Compose** starts the frontend, API, database, and Redis together,
  reducing local setup differences between operating systems.
- **Nginx** serves as the public entry point and routes requests to the
  frontend and API.

## Assumptions

- Docker is available and allowed to download the project’s container images.
- The computer has an available local port 80.
- The supplied example environment settings are suitable only for local
  evaluation. Anyone deploying the app publicly must supply their own secrets
  and review the deployment configuration.
- The administrator is created interactively during startup; there are no
  shared/default admin credentials.
- The SQL in `data/default.sql` provides sample application data and is
  imported after the administrator is created or verified.

## Security and data

The application stores the PostgreSQL database, Redis data, and uploaded files
in Docker-managed volumes. `docker compose down` preserves those volumes. Do
not add `-v` unless you intentionally want to delete the persisted data.
Never commit `.env.production`, real credentials, or private uploaded files.
