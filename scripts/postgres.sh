#!/bin/bash
gcloud secrets versions access latest --secret="env" > .env
APP_DIR="$HOME/E-commerce-Data-Pipeline"

if ! command -v uv &> /dev/null; then
    echo ">>> Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Start Postgres
echo ">>> Starting Postgres..."
docker compose up -d

sleep 20

# Install python package
uv sync

# Run simulate
uv run $APP_DIR/postgres/simulate.py