#!/bin/bash

echo "=========================================="
echo "启动后端服务并查看日志"
echo "=========================================="
echo ""

cd backend

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3"
    exit 1
fi

echo "✅ Python环境检查通过"
echo ""

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 检查依赖
echo "检查依赖..."
python3 -c "import fastapi; import uvicorn; print('✅ 基础依赖已安装')" 2>&1 || {
    echo "⚠️ 依赖可能未安装，正在安装..."
    pip install -q -r requirements_test.txt
}

echo ""
echo "=========================================="
echo "启动后端服务..."
echo "=========================================="
echo ""
echo "📋 提示："
echo "  - 服务地址: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - 按 Ctrl+C 停止服务"
echo ""
echo "=========================================="
echo ""

# 启动服务（直接运行，可以看到实时日志）
python3 start_test.py
