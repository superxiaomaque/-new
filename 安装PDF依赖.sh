#!/bin/bash

echo "=========================================="
echo "安装PDF导出依赖 (reportlab)"
echo "=========================================="
echo ""

cd backend

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

echo "安装 reportlab==4.0.7..."
pip install reportlab==4.0.7

echo ""
echo "✅ 安装完成！"
echo ""
echo "请重启后端服务以使更改生效："
echo "  ./重启后端.sh"
echo ""
