#!/bin/bash

# Install UV

curl -LsSf https://astral.sh/uv/install.sh | sh

# 
source "$HOME/.local/bin/env"

# Start Postgres
echo ">>> Starting Postgres..."
docker compose up -d --no-deps postgres

# Install python package
uv sync

# Run simulate
uv run $APP_DIR/postgres/simulate.py
