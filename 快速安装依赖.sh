#!/bin/bash

echo "=========================================="
echo "快速安装依赖（使用国内镜像）"
echo "=========================================="
echo ""

cd "$(dirname "$0")/backend" || exit 1

echo "正在使用清华镜像源安装依赖..."
echo ""

pip3 install -r requirements_test.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 依赖安装成功！"
    echo "=========================================="
    echo ""
    echo "现在可以启动后端了："
    echo "  python3 start_test.py"
else
    echo ""
    echo "❌ 安装失败，尝试其他方法..."
    echo ""
    echo "方法2: 使用阿里云镜像"
    pip3 install -r requirements_test.txt \
        -i https://mirrors.aliyun.com/pypi/simple/ \
        --trusted-host mirrors.aliyun.com
fi
