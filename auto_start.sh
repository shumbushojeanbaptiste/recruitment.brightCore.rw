#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.prod.yml}"
PYTHON_BIN="${PYTHON_BIN:-}"
HEALTHCHECK_ATTEMPTS="${HEALTHCHECK_ATTEMPTS:-60}"

cd "$ROOT_DIR"

if [[ -z "$PYTHON_BIN" ]]; then
    if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
        PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
    elif [[ "$OSTYPE" == msys* || "$OSTYPE" == cygwin* ]] \
        && [[ -x "$ROOT_DIR/.venv/Scripts/python.exe" ]]; then
        PYTHON_BIN="$ROOT_DIR/.venv/Scripts/python.exe"
    else
        PYTHON_BIN=python
    fi
fi

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

command -v docker >/dev/null 2>&1 || fail "Docker is not installed or is not on PATH."
command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail \
    "Python command '$PYTHON_BIN' was not found. Set PYTHON_BIN to your Python 3.12 executable."
[[ -f "$ENV_FILE" ]] || fail \
    "Missing $ENV_FILE. Add POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, and a generated JWT_SECRET_KEY before starting the stack."
[[ -f "$COMPOSE_FILE" ]] || fail "Missing Compose file: $COMPOSE_FILE"

COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

printf '\n==> 1/8: Run the test suite\n'
"$PYTHON_BIN" -m pytest -q

printf '\n==> 2/8: Validate the production Compose configuration\n'
"${COMPOSE[@]}" config -q

printf '\n==> 3/8: Pull PostgreSQL, Redis, and Nginx images\n'
"${COMPOSE[@]}" pull postgres redis nginx

printf '\n==> 4/8: Build the API image and pull its base image\n'
"${COMPOSE[@]}" build --pull api

printf '\n==> 5/8: Start PostgreSQL and Redis and wait for readiness\n'
"${COMPOSE[@]}" up -d postgres redis

printf '\n==> 6/8: Apply all database schema migrations\n'
"${COMPOSE[@]}" run --rm api alembic upgrade head

printf '\n==> 7/8: Start the API and Nginx\n'
"${COMPOSE[@]}" up -d api nginx

printf 'Waiting for the API readiness endpoint'
api_ready=false
for ((attempt = 1; attempt <= HEALTHCHECK_ATTEMPTS; attempt++)); do
    if "${COMPOSE[@]}" exec -T api python -c \
        'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/health/ready", timeout=3)' \
        >/dev/null 2>&1; then
        api_ready=true
        break
    fi

    printf '.'
    sleep 2
done
printf '\n'

if [[ "$api_ready" != true ]]; then
    "${COMPOSE[@]}" logs --tail 100 api >&2
    fail "The API did not become ready. Review the API logs above and resolve the reported issue."
fi

printf '\n==> 8/8: Create or verify the administrator account\n'
printf 'Enter the admin details when prompted. This does not create a hard-coded default account.\n'
"${COMPOSE[@]}" exec api python -m app.cli.seed_admin

printf '\nMigration state:\n'
"${COMPOSE[@]}" exec -T api alembic current
"${COMPOSE[@]}" exec -T api alembic history

printf '\nRecent API logs:\n'
"${COMPOSE[@]}" logs --tail 100 api

printf '\nBrightCore is ready.\n'
printf 'Application: http://localhost/\n'
printf 'API docs:    http://localhost/docs\n'
printf 'API health:  http://localhost/health/ready\n'
printf '\nService status:\n'
"${COMPOSE[@]}" ps