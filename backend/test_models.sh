#!/bin/bash
# 测试不同模型名称格式

API_KEY="0e2e18c3-b709-4a19-868e-abcdd2c8ed02"
API_URL="https://ark.cn-beijing.volces.com/api/v3/responses"

# 常见的模型名称格式（根据火山引擎文档常见格式）
MODELS=(
    "doubao-seed-1.6-thinking"
    "doubao-seed-1-6-thinking"
    "doubao-pro-4k"
    "doubao-lite-4k"
    "doubao-seed-1.6"
    "doubao-seed-1-6"
    "doubao-seed-thinking"
    "doubao-pro"
    "doubao-lite"
    "doubao-seed"
)

echo "正在测试不同的模型名称..."
echo "使用 API Key: ${API_KEY:0:20}..."
echo ""

for model in "${MODELS[@]}"; do
    echo -n "测试模型: $model ... "
    
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        "$API_URL" \
        -H "Authorization: Bearer $API_KEY" \
        -H 'Content-Type: application/json' \
        -d "{
            \"model\": \"$model\",
            \"input\": [{
                \"role\": \"user\",
                \"content\": [{
                    \"type\": \"input_text\",
                    \"text\": \"你好\"
                }]
            }]
        }" 2>/dev/null)
    
    http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed 's/HTTP_CODE:[0-9]*$//')
    
    if [ "$http_code" = "200" ]; then
        echo "✅ 成功！"
        echo "模型名称: $model"
        echo "响应预览: $(echo "$body" | head -c 200)"
        echo ""
        echo "请在 backend/.env 中设置："
        echo "DOUBAO_MODEL=$model"
        echo ""
        exit 0
    else
        error_msg=$(echo "$body" | grep -o '"message":"[^"]*"' | cut -d'"' -f4 | head -c 50)
        if [ -n "$error_msg" ]; then
            echo "❌ ($error_msg)"
        else
            echo "❌ (HTTP $http_code)"
        fi
    fi
done

echo ""
echo "所有模型名称都测试失败。"
echo "请检查："
echo "1. 火山引擎控制台中的可用模型列表"
echo "2. 火山引擎文档中的模型名称格式"
echo "3. 你的账号是否有权限访问这些模型"
