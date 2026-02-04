#!/bin/bash

echo "=========================================="
echo "重启后端服务"
echo "=========================================="
echo ""

# 停止现有后端服务
echo "1️⃣ 停止现有后端服务..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 2

# 检查是否成功停止
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️ 端口8000仍被占用，尝试强制停止..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# 启动后端服务
echo "2️⃣ 启动后端服务..."
cd backend

# 检查虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 安装新依赖（如果需要）
echo "检查依赖..."
pip install -q reportlab==4.0.7 2>/dev/null

# 启动服务
echo "启动中..."
python start_test.py
