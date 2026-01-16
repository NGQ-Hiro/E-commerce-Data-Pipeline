#!/bin/bash
set -e

# --- 1. SETUP LOGGING ---
# Ghi log ra /var/log/startup_script.log để dễ kiểm tra
exec > >(tee /var/log/startup_script.log|logger -t startup_script -s 2>/dev/console) 2>&1

echo ">>> [ROOT] Bắt đầu cài đặt VM..."

# --- 2. CẤU HÌNH ---
SSH_USER="hieu"
REPO_URL="https://github.com/NGQ-Hiro/E-commerce-Data-Pipeline.git"
APP_DIR="/home/$SSH_USER/E-commerce-Data-Pipeline"

# --- 4. UPDATE & CÀI GIT, DOCKER ---
echo ">>> Cập nhật hệ thống và cài đặt Git, Docker..."
apt-get update && apt-get install -y git

# Cài Docker (nếu chưa có)
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
fi

# Thêm hieu vào nhóm docker (để bạn SSH vào gõ lệnh docker không cần sudo)
usermod -aG docker $SSH_USER

# --- 5. CLONE GITHUB ---
echo ">>> Cloning repository về $APP_DIR..."

# Nếu thư mục chưa có code thì clone
if [ ! -d "$APP_DIR/.git" ]; then
    # Clone bằng quyền Root (nhưng vào thư mục của hieu)
    git clone "$REPO_URL" "$APP_DIR"
else
    echo ">>> Repo đã tồn tại, cập nhật code mới nhất..."
    cd "$APP_DIR" && git pull
fi

# --- 6. PHÂN QUYỀN (QUAN TRỌNG NHẤT) ---
# Vì Root clone nên chủ sở hữu đang là Root. 
# Phải chuyển sang cho hieu để bạn SSH vào có thể sửa file/chạy file.
echo ">>> Chuyển quyền sở hữu folder cho $SSH_USER..."
chown -R $SSH_USER:$SSH_USER "$APP_DIR"

echo ">>> [ROOT] Hoàn tất cài đặt!"