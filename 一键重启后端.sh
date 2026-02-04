#!/bin/bash

echo "=========================================="
echo "一键重启后端服务"
echo "=========================================="
echo ""

cd "$(dirname "$0")/backend" || exit 1

# 停止现有服务
echo "1️⃣ 停止现有后端服务..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 1

# 清理Python缓存
echo "2️⃣ 清理缓存..."
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 启动服务
echo "3️⃣ 启动后端服务..."
echo ""
python3 start_test.py
