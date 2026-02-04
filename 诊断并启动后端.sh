#!/bin/bash

echo "=========================================="
echo "诊断并启动后端服务"
echo "=========================================="
echo ""

cd "$(dirname "$0")/backend" || exit 1

# 1. 检查Python
echo "1️⃣ 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3"
    exit 1
fi
python3 --version
echo ""

# 2. 检查.env文件
echo "2️⃣ 检查配置文件..."
if [ -f ".env" ]; then
    echo "✅ 找到 .env 文件"
    if grep -q "DOUBAO_API_KEY" .env; then
        API_KEY_LEN=$(grep "DOUBAO_API_KEY" .env | cut -d'=' -f2 | tr -d ' ' | wc -c)
        if [ "$API_KEY_LEN" -gt 1 ]; then
            echo "✅ DOUBAO_API_KEY 已配置（长度: $((API_KEY_LEN-1))）"
        else
            echo "⚠️ DOUBAO_API_KEY 为空"
        fi
    else
        echo "⚠️ .env 文件中未找到 DOUBAO_API_KEY"
    fi
else
    echo "⚠️ 未找到 .env 文件（将使用默认配置）"
fi
echo ""

# 3. 检查依赖
echo "3️⃣ 检查Python依赖..."
python3 -c "import fastapi; import uvicorn; import sqlalchemy; print('✅ 基础依赖已安装')" 2>&1 || {
    echo "⚠️ 部分依赖缺失，正在安装..."
    pip3 install -q -r requirements_test.txt 2>&1 | tail -3
}
echo ""

# 4. 测试模块导入
echo "4️⃣ 测试模块导入..."
python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

# 模拟测试模式
import test_config as config_module
sys.modules['config'] = config_module

try:
    from services.doubao_api import DoubaoAPI
    from services.storage import StorageService
    print('✅ 核心模块导入成功')
    
    # 测试初始化
    try:
        api = DoubaoAPI()
        print(f'✅ DoubaoAPI 初始化成功 (Model: {api.model})')
    except Exception as e:
        print(f'❌ DoubaoAPI 初始化失败: {e}')
        sys.exit(1)
        
    try:
        storage = StorageService()
        print('✅ StorageService 初始化成功')
    except Exception as e:
        print(f'❌ StorageService 初始化失败: {e}')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ 模块导入失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" 2>&1

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 模块测试失败，请检查错误信息"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 所有检查通过，启动后端服务..."
echo "=========================================="
echo ""
echo "📋 服务信息："
echo "  - 地址: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - 健康检查: http://localhost:8000/health"
echo ""
echo "💡 提示："
echo "  - 按 Ctrl+C 停止服务"
echo "  - 查看实时日志以诊断问题"
echo ""
echo "=========================================="
echo ""

# 启动服务
python3 start_test.py
