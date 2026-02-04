#!/bin/bash

echo "=========================================="
echo "安装后端依赖"
echo "=========================================="
echo ""

cd "$(dirname "$0")/backend" || exit 1

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "✅ 找到虚拟环境，正在激活..."
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "⚠️  未找到虚拟环境，使用系统 Python"
fi

echo ""
echo "正在安装依赖..."
echo ""

# 安装依赖
pip3 install -r requirements_test.txt

echo ""
echo "=========================================="
echo "✅ 依赖安装完成！"
echo "=========================================="
echo ""
echo "现在可以启动后端服务了："
echo "  python3 start_test.py"
