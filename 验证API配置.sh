#!/bin/bash

echo "=========================================="
echo "验证 API 配置"
echo "=========================================="
echo ""

cd "$(dirname "$0")/backend" || exit 1

# 激活虚拟环境（如果有）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "正在验证 API 配置..."
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
    
    api = DoubaoAPI()
    
    print("✅ API 配置加载成功")
    print(f"   API URL: {api.api_url}")
    print(f"   Model: {api.model}")
    
    api_key = api.api_key
    if api_key:
        key_len = len(api_key)
        print(f"   API Key: {api_key[:10]}...{api_key[-4:]} (长度: {key_len})")
        
        if key_len < 20:
            print("   ⚠️  警告：API Key 长度异常")
        else:
            print("   ✅ API Key 格式正常")
    else:
        print("   ❌ API Key: 未配置")
        sys.exit(1)
    
    print("")
    print("正在测试 API 连接...")
    
    import httpx
    
    test_url = f"{api.api_url}/responses"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
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
        with httpx.Client(timeout=10.0) as client:
            response = client.post(test_url, json=test_payload, headers=headers)
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ API 连接成功！配置正确")
                print("")
                print("==========================================")
                print("✅ 配置验证通过，可以开始使用了！")
                print("==========================================")
            elif response.status_code == 401:
                print("   ❌ API 密钥无效或已过期")
                print("   💡 请检查 API Key 是否正确")
            elif response.status_code == 404:
                print(f"   ❌ 模型 '{api.model}' 不可用")
                print("   💡 请检查模型名称是否正确")
            else:
                print(f"   ⚠️  API 返回错误: {response.status_code}")
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        print(f"   错误信息: {error_data['message']}")
                except:
                    print(f"   响应: {response.text[:200]}")
    except httpx.TimeoutException:
        print("   ❌ 连接超时")
    except httpx.ConnectError:
        print("   ❌ 无法连接到 API 服务器")
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        
except Exception as e:
    print(f"❌ 配置验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

PYTHON_SCRIPT
