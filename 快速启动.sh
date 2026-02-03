#!/bin/bash

echo "=========================================="
echo "朋友圈分析助手 - 快速启动脚本"
echo "=========================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到Node.js，请先安装Node.js"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 启动后端
echo "正在启动后端服务..."
cd backend

# 检查是否已安装依赖
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install -q -r requirements_test.txt

echo "启动后端服务（使用SQLite测试模式）..."
python start_test.py &
BACKEND_PID=$!

cd ..

# 等待后端启动
sleep 3

# 启动前端
echo "正在启动前端服务..."
cd frontend

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "启动前端服务..."
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "=========================================="
echo "✅ 服务启动完成！"
echo "=========================================="
echo "后端地址: http://localhost:8000"
echo "前端地址: http://localhost:3000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
