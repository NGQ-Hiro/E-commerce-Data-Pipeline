#!/bin/bash
set -e  # Dừng ngay nếu có lỗi xảy ra

# --- CẤU HÌNH ---
SSH_USER="hieu"
REPO_URL="https://github.com/username/ten-repo-cua-ban.git"
APP_DIR="/home/$SSH_USER/"

# 1. Cập nhật & Cài Git
apt-get update && apt-get install -y git

# 2. Cài Docker (Dùng script tự động chính chủ của Docker)
# Cách này ngắn hơn nhiều so với việc add key GPG thủ công
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. Cấp quyền Docker cho user (để không phải gõ sudo khi dùng docker)
usermod -aG docker $SSH_USER

# 4. Clone Repo & Phân quyền
# if [ ! -d "$APP_DIR" ]; then
#     git clone "$REPO_URL" "$APP_DIR"
    
#     # Đổi chủ sở hữu từ 'root' sang 'hieu'
#     chown -R $SSH_USER:$SSH_USER "$APP_DIR"
# fi

# echo "--- Cài đặt hoàn tất ---"