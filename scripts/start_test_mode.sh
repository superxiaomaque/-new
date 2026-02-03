#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=========================================="
echo "朋友圈分析助手 - 一键启动（测试模式 SQLite）"
echo "=========================================="
echo ""

echo "[1/4] 启动后端（SQLite）"
cd "$ROOT_DIR/backend"

if [ ! -f ".env" ]; then
  echo "未检测到 backend/.env，将从 env.template 生成默认 .env（可后续修改）"
  cp env.template .env
fi

python3 -m venv .venv >/dev/null 2>&1 || true
source .venv/bin/activate
pip install -q -r requirements_test.txt

python test_main.py &
BACKEND_PID=$!

echo "[2/4] 等待后端启动..."
sleep 2

echo "[3/4] 启动前端"
cd "$ROOT_DIR/frontend"
npm install
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "✅ 启动完成"
echo "前端：http://localhost:3000"
echo "后端：http://localhost:8000"
echo "API 文档：http://localhost:8000/docs"
echo "按 Ctrl+C 停止"
echo "=========================================="

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit" INT TERM
wait

