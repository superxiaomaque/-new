#!/bin/bash

echo "=========================================="
echo "完全回退到 0f2c0fc 版本"
echo "=========================================="
echo ""
echo "⚠️  警告：这将丢弃所有未提交的修改！"
echo ""
read -p "确认要继续吗？(y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

cd "$(dirname "$0")" || exit 1

echo ""
echo "正在回退所有修改..."
git checkout 0f2c0fc -- .

echo ""
echo "清理缓存文件..."
find backend -name "*.pyc" -delete
find backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "✅ 回退完成！"
echo ""
echo "注意："
echo "1. 如果仍然失败，可能是 0f2c0fc 版本本身的问题"
echo "2. 建议检查后端启动日志"
echo "3. 可能需要手动修复 cost_monitor.py 的导入问题"
