#!/bin/bash
# 测试不同模型名称格式的脚本

API_KEY="0e2e18c3-b709-4a19-868e-abcdd2c8ed02"
API_URL="https://ark.cn-beijing.volces.com/api/v3/responses"

# 常见的模型名称格式
MODELS=(
    "doubao-seed-1.6-thinking"
    "doubao-seed-1-6-thinking"
    "doubao-pro-4k"
    "doubao-lite-4k"
    "doubao-seed-1.6"
    "doubao-seed-1-6"
    "doubao-seed-thinking"
)

echo "正在测试不同的模型名称..."
echo ""

for model in "${MODELS[@]}"; do
    echo "测试模型: $model"
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
        }")
    
    http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed 's/HTTP_CODE:[0-9]*$//')
    
    if [ "$http_code" = "200" ]; then
        echo "✅ 成功！模型名称: $model"
        echo "响应: $body"
        echo ""
        break
    else
        echo "❌ 失败 (HTTP $http_code)"
        echo "错误: $body" | head -c 200
        echo ""
        echo ""
    fi
done

echo "测试完成！"
