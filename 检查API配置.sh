#!/bin/bash

echo "=========================================="
echo "检查 API 配置"
echo "=========================================="
echo ""

cd "$(dirname "$0")/backend" || exit 1

# 激活虚拟环境（如果有）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "1️⃣ 检查配置文件..."
echo ""

# 检查 .env 文件
if [ -f ".env" ]; then
    echo "✅ 找到 .env 文件"
    
    # 检查 API Key
    API_KEY=$(grep "DOUBAO_API_KEY" .env | cut -d'=' -f2 | tr -d ' ' | tr -d '"')
    if [ -n "$API_KEY" ] && [ "$API_KEY" != "" ]; then
        API_KEY_LEN=${#API_KEY}
        echo "   ✅ DOUBAO_API_KEY: 已配置（长度: $API_KEY_LEN）"
        echo "      前10位: ${API_KEY:0:10}..."
    else
        echo "   ❌ DOUBAO_API_KEY: 未配置或为空"
    fi
    
    # 检查 Model
    MODEL=$(grep "DOUBAO_MODEL" .env | cut -d'=' -f2 | tr -d ' ' | tr -d '"')
    if [ -n "$MODEL" ] && [ "$MODEL" != "" ]; then
        echo "   ✅ DOUBAO_MODEL: $MODEL"
    else
        echo "   ⚠️  DOUBAO_MODEL: 使用默认值"
    fi
    
    # 检查 API URL
    API_URL=$(grep "DOUBAO_API_URL" .env | cut -d'=' -f2 | tr -d ' ' | tr -d '"')
    if [ -n "$API_URL" ] && [ "$API_URL" != "" ]; then
        echo "   ✅ DOUBAO_API_URL: $API_URL"
    else
        echo "   ⚠️  DOUBAO_API_URL: 使用默认值"
    fi
else
    echo "⚠️  未找到 .env 文件，将使用默认配置"
fi

echo ""
echo "2️⃣ 测试 API 配置加载..."
echo ""

python3 << 'PYTHON_SCRIPT'
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    # 模拟测试模式
    import test_config as config_module
    sys.modules['config'] = config_module
    
    from services.doubao_api import DoubaoAPI
    
    print("✅ 配置加载成功")
    print("")
    
    api = DoubaoAPI()
    print(f"   API URL: {api.api_url}")
    print(f"   Model: {api.model}")
    
    api_key = api.api_key
    if api_key:
        key_len = len(api_key)
        print(f"   API Key: {api_key[:10]}...{api_key[-4:]} (长度: {key_len})")
        
        if key_len < 20:
            print("   ⚠️  警告：API Key 长度异常，可能配置不正确")
    else:
        print("   ❌ API Key: 未配置（空）")
        print("   ⚠️  这会导致分析功能无法使用")
    
    print("")
    print("3️⃣ 测试 API 连接...")
    print("")
    
    if not api_key:
        print("   ⚠️  跳过连接测试（API Key 未配置）")
    else:
        import httpx
        
        # 测试连接
        test_url = f"{api.api_url}/responses"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # 简单的测试请求
        test_payload = {
            'model': api.model,
            'input': [{
                'role': 'user',
                'content': [{
                    'type': 'input_text',
                    'text': '你好'
                }]
            }]
        }
        
        try:
            print("   正在连接 API...")
            with httpx.Client(timeout=10.0) as client:
                response = client.post(test_url, json=test_payload, headers=headers)
                
                print(f"   状态码: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ API 连接成功！配置正确")
                elif response.status_code == 401:
                    print("   ❌ API 密钥无效或已过期")
                    print("   💡 请检查 .env 文件中的 DOUBAO_API_KEY")
                elif response.status_code == 404:
                    print(f"   ❌ API 端点不存在或模型 '{api.model}' 不可用")
                    print("   💡 请检查模型名称是否正确")
                else:
                    print(f"   ⚠️  API 返回错误: {response.status_code}")
                    try:
                        error_data = response.json()
                        if 'message' in error_data:
                            print(f"   错误信息: {error_data['message']}")
                        else:
                            print(f"   错误详情: {error_data}")
                    except:
                        error_text = response.text[:200]
                        print(f"   响应内容: {error_text}")
        except httpx.TimeoutException:
            print("   ❌ 连接超时（10秒）")
            print("   💡 请检查网络连接")
        except httpx.ConnectError:
            print("   ❌ 无法连接到 API 服务器")
            print("   💡 请检查网络连接或 API URL 是否正确")
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
except Exception as e:
    print(f"❌ 配置检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
