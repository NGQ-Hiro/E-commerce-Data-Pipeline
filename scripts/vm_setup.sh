#!/bin/bash
set -e  # Dừng ngay nếu có lỗi xảy ra

# --- CẤU HÌNH ---
SSH_USER="hieu"
REPO_URL="https://github.com/NGQ-Hiro/E-commerce-Data-Pipeline.git"
APP_DIR="/home/$SSH_USER/E-commerce-Data-Pipeline"
ENV="/home/$SSH_USER/E-commerce-Data-Pipeline/.env"

# Cập nhật & Cài Git
apt-get update && apt-get install -y git

# Cài Docker (Dùng script tự động chính chủ của Docker)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Cấp quyền Docker cho user (để không phải gõ sudo khi dùng docker)
usermod -aG docker $SSH_USER

# Clone Repo & Phân quyền
if [ ! -d "$APP_DIR" ]; then
    git clone "$REPO_URL" "$APP_DIR"
    
    # Đổi chủ sở hữu từ 'root' sang 'hieu'
    chown -R $SSH_USER:$SSH_USER "$APP_DIR"
fi

echo "--- Cài đặt hoàn tất ---"

# Download .env file
cd $APP_DIR
gcloud secrets versions access latest --secret="env" > .env

# Load biến môi trường từ .env
if [ -f "$ENV" ]; then
  set -a
  source "$ENV"
  set +a
else
  echo "❌ .env not found: $ENV" >&2
  exit 1
fi

# Flow control for each service
SERVICE_NAME="${target_serivce}"
echo ">>> Target Service: $SERVICE_NAME"

if [ "$SERVICE_NAME" == "postgres" ]; then
    # Case A: Postgres -> Chỉ up container rồi xong
    source $APP_DIR/scripts/debezium.sh
    
elif [ "$SERVICE_NAME" == "debezium" ]; then
    # Case B: Debezium -> Up container -> Gọi script phụ
    echo ">>> Calling external script to wait for Postgres..."
    # GỌI FILE SCRIPT PHỤ
    source $APP_DIR/scripts/debezium.sh

elif [ "$SERVICE_NAME" == "airflow" ]; then
    # Case C: Airflow -> Up container -> Gọi script phụ
    echo ">>> Starting Airflow..."
    docker compose up -d --no-deps airflow
    
    echo ">>> Calling external script to wait for Airflow..."
    # GỌI FILE SCRIPT PHỤ
    source $APP_DIR/scripts/airflow.sh
else
    echo "Unknown service!"
fi