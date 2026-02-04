#!/bin/bash

echo "=========================================="
echo "修复 SSL 证书问题并安装依赖"
echo "=========================================="
echo ""

cd "$(dirname "$0")/backend" || exit 1

echo "方法1: 使用国内镜像源（推荐，速度快）"
echo ""

# 使用清华镜像源安装
pip3 install -r requirements_test.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 依赖安装成功！"
    exit 0
fi

echo ""
echo "方法1失败，尝试方法2..."
echo ""

# 方法2: 使用阿里云镜像
pip3 install -r requirements_test.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 依赖安装成功！"
    exit 0
fi

echo ""
echo "方法2失败，尝试方法3（临时禁用SSL验证，不推荐但可用）..."
echo ""

# 方法3: 临时禁用SSL验证
pip3 install -r requirements_test.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 依赖安装成功！"
    exit 0
fi

echo ""
echo "❌ 所有方法都失败了"
echo "请尝试手动安装证书："
echo "  /Applications/Python\\ 3.12/Install\\ Certificates.command"
echo ""
echo "或者使用虚拟环境："
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements_test.txt"
