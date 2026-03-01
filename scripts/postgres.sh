#!/bin/bash
gcloud secrets versions access latest --secret="env" > .env
APP_DIR="$HOME/E-commerce-Data-Pipeline"

if ! command -v uv &> /dev/null; then
    echo ">>> Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install tmux nếu chưa có
if ! command -v tmux &> /dev/null; then
    echo ">>> Installing tmux..."
    sudo apt update
    sudo apt install -y tmux
fi


# Start Postgres
echo ">>> Starting Postgres..."
docker compose up -d

sleep 30

# Install python package
uv sync

# Start simulate in tmux
SESSION_NAME="simulate_session"

if ! tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo ">>> Starting simulate in tmux..."
    tmux new-session -d -s $SESSION_NAME \
    "uv run $APP_DIR/postgres/simulate.py >> simulate.log 2>&1"
else
    echo ">>> Session already exists"
fi

echo ">>> Done"
echo "Attach using: tmux attach -t $SESSION_NAME"