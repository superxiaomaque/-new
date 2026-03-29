<template>
  <div class="result-container">
    <van-nav-bar title="分析结果" left-arrow @click-left="$router.back()" />
    
    <div v-if="loading" class="loading-container">
      <van-loading type="spinner" size="24px">加载中...</van-loading>
    </div>
    
    <div v-else-if="result" class="content">
      <!-- 匹配度评分 -->
      <div class="score-card">
        <div class="score-item">
          <div class="score-value">{{ result.match_score || 0 }}</div>
          <div class="score-label">匹配度</div>
        </div>
        <div class="score-item">
          <div class="score-value">{{ result.success_rate || 0 }}%</div>
          <div class="score-label">脱单成功率</div>
        </div>
      </div>
      
      <!-- 可折叠的分析结果 -->
      <van-collapse v-model="activeNames" accordion>
        <van-collapse-item title="性格分析" name="personality">
          <div class="result-content">{{ result.personality || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="兴趣爱好" name="interests">
          <div class="result-content">{{ result.interests || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="价值观倾向" name="values">
          <div class="result-content">{{ result.values || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="情感状态" name="emotion">
          <div class="result-content">{{ result.emotion || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="收入与消费能力" name="income_analysis">
          <div class="result-content">{{ result.income_analysis || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="沟通建议" name="communication">
          <div class="result-content">
            <div v-if="result.communication.topics && result.communication.topics.length > 0">
              <h4>推荐话题：</h4>
              <ul>
                <li v-for="(topic, index) in result.communication.topics" :key="index">{{ topic }}</li>
              </ul>
            </div>
            <div v-if="result.communication.opening_lines && result.communication.opening_lines.length > 0">
              <h4>开场白建议：</h4>
              <ul>
                <li v-for="(line, index) in result.communication.opening_lines" :key="index">{{ line }}</li>
              </ul>
            </div>
            <div v-if="result.communication.tips">
              <h4>聊天技巧：</h4>
              <p>{{ result.communication.tips }}</p>
            </div>
          </div>
        </van-collapse-item>
        <van-collapse-item title="关系推进建议" name="relationship">
          <div class="result-content">{{ result.relationship || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="避雷指南" name="warnings">
          <div class="result-content">{{ result.warnings || '暂无数据' }}</div>
        </van-collapse-item>
      </van-collapse>
      
      <!-- 多轮对话 -->
      <div class="chat-section">
        <h3>继续追问</h3>
        <div class="chat-messages">
          <div
            v-for="(msg, index) in chatMessages"
            :key="index"
            :class="['chat-message', msg.role]"
          >
            <div class="message-content">{{ msg.content }}</div>
          </div>
        </div>
        <div class="chat-input">
          <van-field
            v-model="chatInput"
            placeholder="输入您的问题..."
            @keyup.enter="sendMessage"
          >
            <template #button>
              <van-button size="small" type="primary" @click="sendMessage">发送</van-button>
            </template>
          </van-field>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="actions">
        <van-button round block type="primary" @click="shareResult">
          分享结果
        </van-button>
        <van-button round block @click="exportResult">
          导出图片
        </van-button>
      </div>
    </div>
    
    <van-empty v-else description="暂无数据" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import api from '../api'

const route = useRoute()
const analysisId = route.params.id

const loading = ref(true)
const result = ref(null)
const activeNames = ref('personality')
const chatMessages = ref([])
const chatInput = ref('')

const loadResult = async () => {
  try {
    const response = await api.get(`/analyses/${analysisId}`)
    const data = response.data.result
    const incomeRaw =
      data.income_analysis ??
      data.incomeAnalysis ??
      data.income_and_consumption ??
      data.consumption_analysis ??
      data.lifestyle
    const formatIncome = (v) => {
      if (v == null || v === '') return '暂无数据'
      if (typeof v === 'string') return v
      try {
        return JSON.stringify(v, null, 2)
      } catch {
        return String(v)
      }
    }
    // 处理分析结果，确保所有字段都有值
    result.value = {
      match_score: data.match_score || 0,
      success_rate: data.success_rate || 0,
      personality: data.personality || '暂无数据',
      interests: data.interests || '暂无数据',
      values: data.values || '暂无数据',
      emotion: data.emotion || '暂无数据',
      income_analysis: formatIncome(incomeRaw),
      communication: data.communication || {
        topics: [],
        opening_lines: [],
        tips: '暂无数据'
      },
      relationship: data.relationship || '暂无数据',
      warnings: data.warnings || '暂无数据',
      summary: data.summary || ''
    }
  } catch (error) {
    showToast({ type: 'fail', message: '加载失败' })
  } finally {
    loading.value = false
  }
}

const sendMessage = async () => {
  if (!chatInput.value.trim()) return
  
  const userMessage = {
    role: 'user',
    content: chatInput.value
  }
  chatMessages.value.push(userMessage)
  const question = chatInput.value
  chatInput.value = ''
  
  try {
    const response = await api.post(`/analyses/${analysisId}/chat`, {
      question
    })
    chatMessages.value.push({
      role: 'assistant',
      content: response.data.answer
    })
  } catch (error) {
    showToast({ type: 'fail', message: '发送失败' })
    chatMessages.value.pop()
  }
}

const shareResult = async () => {
  try {
    const res = await api.post(`/shares/${analysisId}`)
    const sharePath = res.data.share_url // 形如 /share/{token}
    const shareUrl = `${window.location.origin}${sharePath}`

    // 优先使用系统分享（部分浏览器支持）
    if (navigator.share) {
      try {
        await navigator.share({
          title: '朋友圈截图分析结果',
          text: '我用AI生成了一份朋友圈截图分析报告（不含原图）',
          url: shareUrl
        })
        showToast({ type: 'success', message: '分享成功' })
        return
      } catch (e) {
        // 用户取消分享，继续执行复制链接
      }
    }

    // 复制链接到剪贴板
    await navigator.clipboard.writeText(shareUrl)
    showToast({ type: 'success', message: '分享链接已复制到剪贴板' })
  } catch (e) {
    showToast({ type: 'fail', message: e?.response?.data?.detail || '生成分享链接失败' })
  }
}

const exportResult = async () => {
  try {
    const res = await api.get(`/analyses/${analysisId}/export.png`, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'image/png' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `analysis_${analysisId}.png`
    a.click()
    URL.revokeObjectURL(url)
    showToast({ type: 'success', message: '已开始下载' })
  } catch (e) {
    showToast({ type: 'fail', message: e?.response?.data?.detail || '导出失败' })
  }
}

onMounted(() => {
  loadResult()
})
</script>

<style scoped>
.result-container {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 20px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
}

.content {
  padding: 10px;
}

.score-card {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-around;
}

.score-item {
  text-align: center;
}

.score-value {
  font-size: 36px;
  font-weight: bold;
  color: white;
  margin-bottom: 5px;
}

.score-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.result-content {
  padding: 15px;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
}

.chat-section {
  background: white;
  border-radius: 12px;
  padding: 15px;
  margin-top: 10px;
}

.chat-section h3 {
  font-size: 16px;
  margin-bottom: 15px;
  color: #333;
}

.chat-messages {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 15px;
}

.chat-message {
  margin-bottom: 15px;
}

.chat-message.user {
  text-align: right;
}

.message-content {
  display: inline-block;
  max-width: 70%;
  padding: 10px 15px;
  border-radius: 12px;
  background: #f0f0f0;
  color: #333;
  word-wrap: break-word;
}

.result-content h4 {
  font-size: 16px;
  font-weight: bold;
  margin: 15px 0 10px 0;
  color: #333;
}

.result-content ul {
  margin: 10px 0;
  padding-left: 20px;
}

.result-content li {
  margin: 8px 0;
  line-height: 1.6;
}

.chat-message.user .message-content {
  background: #ff6b9d;
  color: white;
}

.actions {
  margin-top: 20px;
  padding: 0 10px;
  display: flex;
  gap: 10px;
}

.actions .van-button {
  flex: 1;
}
</style>
