<template>
  <div class="upload-container">
    <van-nav-bar 
      :title="showResult ? '分析结果' : '上传截图'" 
      :left-arrow="!showResult"
      @click-left="handleBack"
    />
    
    <!-- 上传界面 -->
    <div v-if="!showResult" class="content">
      <div class="upload-area">
        <van-uploader
          v-model="fileList"
          multiple
          :max-count="20"
          :max-size="10 * 1024 * 1024"
          :after-read="afterRead"
          :before-delete="beforeDelete"
          accept="image/*"
          :preview-full-image="true"
        >
          <div class="upload-slot">
            <van-icon name="plus" size="40" />
            <p>点击或拖拽上传</p>
            <p class="hint">最多20张，单张不超过10MB</p>
          </div>
        </van-uploader>
        
        <div v-if="fileList.length > 0" class="upload-tip">
          <van-icon name="info-o" />
          <span>已上传 {{ fileList.length }} 张，至少需要 5 张</span>
        </div>
      </div>
      
      <div class="supplementary-info">
        <van-cell-group inset title="补充信息（可选）">
          <van-field
            v-model="supplementaryInfo.gender"
            label="性别"
            placeholder="请选择"
            readonly
            is-link
            @click="showGenderPicker = true"
          />
          <van-field
            v-model="supplementaryInfo.age"
            label="年龄"
            placeholder="请输入年龄"
            type="number"
          />
          <van-field
            v-model="supplementaryInfo.occupation"
            label="职业"
            placeholder="请输入职业"
          />
          <van-field
            v-model="supplementaryInfo.relationship"
            label="关系"
            placeholder="请输入关系（如：朋友、同事等）"
          />
        </van-cell-group>
      </div>
      
      <div class="submit-btn">
        <van-button
          round
          block
          type="primary"
          size="large"
          :disabled="fileList.length < 5"
          :loading="analyzing"
          @click="submitAnalysis"
        >
          {{ analyzing ? '分析中...' : '开始分析' }}
        </van-button>
      </div>
    </div>

    <!-- 结果展示界面 -->
    <div v-else class="result-content">
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
            <div class="result-content-text">{{ formatResult(result.personality) }}</div>
          </van-collapse-item>
          <van-collapse-item title="兴趣爱好" name="interests">
            <div class="result-content-text">{{ formatResult(result.interests) }}</div>
          </van-collapse-item>
          <van-collapse-item title="价值观倾向" name="values">
            <div class="result-content-text">{{ formatResult(result.values) }}</div>
          </van-collapse-item>
          <van-collapse-item title="情感状态" name="emotion">
            <div class="result-content-text">{{ formatResult(result.emotion) }}</div>
          </van-collapse-item>
          <van-collapse-item title="沟通建议" name="communication">
            <div class="result-content-text">
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
            <div class="result-content-text">{{ formatResult(result.relationship) }}</div>
          </van-collapse-item>
          <van-collapse-item title="避雷指南" name="warnings">
            <div class="result-content-text">{{ formatResult(result.warnings) }}</div>
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
          <van-button round block @click="resetAnalysis" style="margin-top: 10px;">
            重新分析
          </van-button>
        </div>
      </div>
      
      <van-empty v-else description="暂无数据" />
    </div>

    <!-- 分析中弹窗（趣味动画 + 进度） -->
    <van-popup v-model:show="showProgress" round position="center">
      <div class="progress-card">
        <div class="hearts">
          <span class="heart h1">❤</span>
          <span class="heart h2">❤</span>
          <span class="heart h3">❤</span>
        </div>
        <div class="progress-title">{{ progressTip }}</div>
        <van-progress :percentage="progress" stroke-width="10" color="#ff6b9d" />
        <div class="progress-sub">{{ progress }}%</div>
      </div>
    </van-popup>
    
    <!-- 性别选择器 -->
    <van-popup v-model:show="showGenderPicker" position="bottom">
      <van-picker
        :columns="genderOptions"
        @confirm="onGenderConfirm"
        @cancel="showGenderPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import api from '../api'

const router = useRouter()

// 上传相关状态
const fileList = ref([])
const analyzing = ref(false)
const showGenderPicker = ref(false)
const showProgress = ref(false)
const progress = ref(0)
const progressTip = ref('AI正在深度思考中...')
let progressTimer = null

// 结果相关状态
const showResult = ref(false)
const loading = ref(false)
const result = ref(null)
const analysisId = ref(null)
const activeNames = ref('personality')
const chatMessages = ref([])
const chatInput = ref('')

const genderOptions = [
  { text: '男', value: 'male' },
  { text: '女', value: 'female' },
  { text: '未知', value: 'unknown' }
]

const supplementaryInfo = ref({
  gender: '',
  age: '',
  occupation: '',
  relationship: ''
})

const afterRead = (file) => {
  console.log('文件读取完成', file)
}

const beforeDelete = async (file, detail) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '确定要删除这张图片吗？'
    })
    return true
  } catch {
    return false
  }
}

const onGenderConfirm = ({ selectedOptions }) => {
  supplementaryInfo.value.gender = selectedOptions[0].text
  showGenderPicker.value = false
}

const startProgress = () => {
  showProgress.value = true
  progress.value = 1
  const tips = [
    'AI正在读取截图内容...',
    '正在洞察性格与偏好...',
    '正在生成追爱策略...',
    '正在输出匹配度评分...',
    '正在整理避雷指南...'
  ]
  let i = 0
  progressTip.value = tips[i]

  if (progressTimer) clearInterval(progressTimer)
  progressTimer = setInterval(() => {
    if (progress.value < 90) {
      progress.value += Math.random() > 0.6 ? 2 : 1
      if (progress.value % 18 === 0) {
        i = Math.min(i + 1, tips.length - 1)
        progressTip.value = tips[i]
      }
    }
  }, 450)
}

const stopProgress = () => {
  if (progressTimer) clearInterval(progressTimer)
  progressTimer = null
  progress.value = 100
  setTimeout(() => {
    showProgress.value = false
    progress.value = 0
  }, 500)
}

const formatResult = (value) => {
  if (Array.isArray(value)) {
    return value.join('、')
  }
  return value || '暂无数据'
}

const submitAnalysis = async () => {
  if (fileList.value.length < 5) {
    showToast({ type: 'fail', message: '至少需要上传5张图片' })
    return
  }
  
  analyzing.value = true
  startProgress()
  
  try {
    const formData = new FormData()
    fileList.value.forEach((file) => {
      formData.append('images', file.file)
    })
    formData.append('supplementary_info', JSON.stringify(supplementaryInfo.value))
    
    const response = await api.post('/analyses', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000
    })
    
    // 保存分析ID和结果
    analysisId.value = response.data.id
    const data = response.data.result
    
    // 处理分析结果，确保所有字段都有值
    result.value = {
      match_score: data.match_score || 0,
      success_rate: data.success_rate || 0,
      personality: data.personality || '暂无数据',
      interests: data.interests || '暂无数据',
      values: data.values || '暂无数据',
      emotion: data.emotion || '暂无数据',
      communication: data.communication || {
        topics: [],
        opening_lines: [],
        tips: '暂无数据'
      },
      relationship: data.relationship || '暂无数据',
      warnings: data.warnings || '暂无数据',
      summary: data.summary || ''
    }
    
    // 切换到结果展示
    showResult.value = true
    showToast({ type: 'success', message: '分析完成' })
  } catch (error) {
    console.error('分析失败', error)
    showToast({ type: 'fail', message: error.response?.data?.detail || '分析失败，请重试' })
  } finally {
    analyzing.value = false
    stopProgress()
  }
}

const sendMessage = async () => {
  if (!chatInput.value.trim() || !analysisId.value) return
  
  const userMessage = {
    role: 'user',
    content: chatInput.value
  }
  chatMessages.value.push(userMessage)
  const question = chatInput.value
  chatInput.value = ''
  
  try {
    const response = await api.post(`/analyses/${analysisId.value}/chat`, {
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
  if (!analysisId.value) return
  
  try {
    const res = await api.post(`/shares/${analysisId.value}`)
    const sharePath = res.data.share_url
    const shareUrl = `${window.location.origin}${sharePath}`

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

    await navigator.clipboard.writeText(shareUrl)
    showToast({ type: 'success', message: '分享链接已复制到剪贴板' })
  } catch (e) {
    showToast({ type: 'fail', message: e?.response?.data?.detail || '生成分享链接失败' })
  }
}

const exportResult = async () => {
  if (!analysisId.value) return
  
  try {
    const res = await api.get(`/analyses/${analysisId.value}/export.png`, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'image/png' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `analysis_${analysisId.value}.png`
    a.click()
    URL.revokeObjectURL(url)
    showToast({ type: 'success', message: '已开始下载' })
  } catch (e) {
    showToast({ type: 'fail', message: e?.response?.data?.detail || '导出失败' })
  }
}

const resetAnalysis = () => {
  // 重置所有状态，回到上传界面
  showResult.value = false
  result.value = null
  analysisId.value = null
  chatMessages.value = []
  chatInput.value = ''
  fileList.value = []
  supplementaryInfo.value = {
    gender: '',
    age: '',
    occupation: '',
    relationship: ''
  }
  activeNames.value = 'personality'
}

const handleBack = () => {
  if (showResult.value) {
    resetAnalysis()
  } else {
    router.back()
  }
}

onBeforeUnmount(() => {
  if (progressTimer) clearInterval(progressTimer)
})
</script>

<style scoped>
.upload-container {
  min-height: 100vh;
  background: #f5f5f5;
}

.content {
  padding: 10px;
}

.upload-area {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 10px;
}

.upload-slot {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.upload-slot p {
  margin: 10px 0;
  font-size: 14px;
}

.upload-slot .hint {
  font-size: 12px;
  color: #ccc;
}

.upload-tip {
  margin-top: 15px;
  padding: 10px;
  background: #fff7e6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #ed6a00;
}

.supplementary-info {
  margin-bottom: 20px;
}

.submit-btn {
  padding: 0 10px 20px;
}

.progress-card {
  width: 320px;
  padding: 22px 18px 18px;
  background: white;
  border-radius: 16px;
}

.hearts {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 12px;
}

.heart {
  font-size: 22px;
  color: #ff6b9d;
  animation: pulse 1.2s infinite ease-in-out;
}

.heart.h2 {
  animation-delay: 0.2s;
}

.heart.h3 {
  animation-delay: 0.4s;
}

.progress-title {
  text-align: center;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.progress-sub {
  text-align: center;
  color: #999;
  margin-top: 10px;
  font-size: 12px;
}

@keyframes pulse {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.15); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

/* 结果展示样式 */
.result-content {
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

.score-card {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  border-radius: 12px;
  padding: 30px;
  margin: 10px;
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

.result-content-text {
  padding: 15px;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
}

.result-content-text h4 {
  font-size: 16px;
  font-weight: bold;
  margin: 15px 0 10px 0;
  color: #333;
}

.result-content-text ul {
  margin: 10px 0;
  padding-left: 20px;
}

.result-content-text li {
  margin: 8px 0;
  line-height: 1.6;
}

.chat-section {
  background: white;
  border-radius: 12px;
  padding: 15px;
  margin: 10px;
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

.chat-message.user .message-content {
  background: #ff6b9d;
  color: white;
}

.actions {
  margin-top: 20px;
  padding: 0 10px;
}

.actions .van-button {
  margin-bottom: 10px;
}
</style>
