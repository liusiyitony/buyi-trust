#!/bin/bash
# Buyi Trust Protocol — Run server
# Usage: ./run.sh [port]

PORT=${1:-8398}
cd "$(dirname "$0")"

# Create venv if needed
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    .venv/bin/pip install flask gunicorn
fi

# Init DB
.venv/bin/python -c "from db import init_db; init_db()"

# Run with gunicorn
.venv/bin/gunicorn app:create_app() \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile -
