<template>
  <div class="home-container">
    <!-- 顶部标题区域 -->
    <div class="header">
      <div class="header-content">
        <h1 class="title">朋友圈分析助手</h1>
        <p class="subtitle">通过AI分析，助您找到心仪的另一半</p>
      </div>
    </div>
    
    <!-- 上传区域（始终显示，但显示不同状态） -->
    <div class="upload-section" :class="{ 'has-result': showResult }">
      <div class="upload-card" :class="{ 'uploaded': fileList.length > 0 }">
        <div v-if="fileList.length === 0" class="upload-empty">
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
              <div class="upload-icon-wrapper">
                <van-icon name="plus" size="32" />
              </div>
              <p class="upload-text">点击或拖拽上传</p>
              <p class="upload-hint">最多20张，单张不超过10MB</p>
            </div>
          </van-uploader>
        </div>
        
        <div v-else class="upload-status">
          <div class="status-header">
            <div class="status-icon-wrapper">
              <van-icon name="success" size="18" />
            </div>
            <span class="status-text">已上传 <strong>{{ fileList.length }}</strong> 张图片</span>
            <van-button 
              size="mini" 
              type="primary" 
              plain
              round
              @click="fileList = []"
              class="reset-btn"
            >
              重新上传
            </van-button>
          </div>
          <div class="upload-preview">
            <van-uploader
              v-model="fileList"
              multiple
              :max-count="20"
              :max-size="10 * 1024 * 1024"
              :after-read="afterRead"
              :before-delete="beforeDelete"
              accept="image/*"
              :preview-full-image="true"
              :show-upload="fileList.length < 20"
            />
          </div>
        </div>
      </div>
      
      <div class="actions-wrapper">
        <van-button
          round
          block
          type="primary"
          size="large"
          :disabled="fileList.length < 5"
          :loading="analyzing"
          @click="submitAnalysis"
          class="analyze-btn"
        >
          <span v-if="!analyzing">
            <van-icon name="search" /> 开始分析
          </span>
          <span v-else>分析中...</span>
        </van-button>
        <div v-if="fileList.length > 0 && fileList.length < 5" class="tip-text">
          <van-icon name="info-o" /> 至少需要 5 张图片才能开始分析
        </div>
      </div>
    </div>

    <!-- 结果展示区域（显示在上传模块下方） -->
    <transition name="fade-slide">
      <div v-if="showResult && result" class="result-section">
        <!-- 匹配度评分卡片 -->
        <div class="score-card">
          <div class="score-item">
            <div class="score-value-wrapper">
              <span class="score-value">{{ result.match_score || 0 }}</span>
              <span class="score-unit">分</span>
            </div>
            <div class="score-label">匹配度</div>
          </div>
          <div class="score-divider"></div>
          <div class="score-item">
            <div class="score-value-wrapper">
              <span class="score-value">{{ result.success_rate || 0 }}</span>
              <span class="score-unit">%</span>
            </div>
            <div class="score-label">脱单成功率</div>
          </div>
        </div>
        
        <!-- 分析结果卡片组 -->
        <div class="analysis-cards">
          <transition-group name="card-fade" tag="div">
            <div 
              v-for="item in analysisItems" 
              :key="item.name"
              class="analysis-card"
              :class="{ 'expanded': activeNames.includes(item.name) }"
            >
              <div 
                class="card-header"
                @click="toggleCard(item.name)"
              >
                <div class="card-title-wrapper">
                  <van-icon :name="item.icon" class="card-icon" />
                  <span class="card-title">{{ item.title }}</span>
                </div>
                <van-icon 
                  :name="activeNames.includes(item.name) ? 'arrow-up' : 'arrow-down'" 
                  class="card-arrow"
                />
              </div>
              <transition name="expand">
                <div v-if="activeNames.includes(item.name)" class="card-content">
                  <div class="result-content-text">{{ formatResult(item.content) }}</div>
                </div>
              </transition>
            </div>
          </transition-group>
        </div>
        
        <!-- 多轮对话 -->
        <div class="chat-section">
          <div class="chat-header">
            <van-icon name="chat-o" />
            <h3>继续追问</h3>
          </div>
          <div class="chat-messages" ref="chatMessagesRef">
            <transition-group name="message-fade" tag="div">
              <div
                v-for="(msg, index) in chatMessages"
                :key="index"
                :class="['chat-message', msg.role]"
              >
                <div class="message-content">{{ msg.content }}</div>
              </div>
            </transition-group>
          </div>
          <div class="chat-input-wrapper">
            <van-field
              v-model="chatInput"
              placeholder="输入您的问题..."
              @keyup.enter="sendMessage"
              class="chat-field"
            >
              <template #button>
                <van-button 
                  size="small" 
                  type="primary" 
                  round
                  @click="sendMessage"
                  :disabled="!chatInput.trim()"
                >
                  发送
                </van-button>
              </template>
            </van-field>
          </div>
        </div>
        
        <!-- 操作按钮（优化布局） -->
        <div class="result-actions">
          <div class="action-row">
            <van-button 
              round 
              block 
              type="primary" 
              @click="shareResult"
              class="action-btn"
            >
              <van-icon name="share-o" /> 分享结果
            </van-button>
            <van-button 
              round 
              block 
              @click="exportResult"
              class="action-btn secondary"
            >
              <van-icon name="down" /> 导出图片
            </van-button>
          </div>
          <van-button 
            round 
            block 
            @click="resetAnalysis" 
            class="reset-analysis-btn"
          >
            <van-icon name="replay" /> 重新分析
          </van-button>
        </div>
      </div>
    </transition>

    <!-- 分析中弹窗（高级动画） -->
    <van-popup 
      v-model:show="showProgress" 
      round 
      position="center"
      :close-on-click-overlay="false"
      class="progress-popup"
    >
      <div class="progress-card">
        <div class="progress-header">
          <div class="hearts">
            <span class="heart h1">❤</span>
            <span class="heart h2">❤</span>
            <span class="heart h3">❤</span>
          </div>
        </div>
        <div class="progress-title">{{ progressTip }}</div>
        <div class="progress-bar-wrapper">
          <van-progress 
            :percentage="progress" 
            stroke-width="8" 
            color="linear-gradient(90deg, #ff6b9d 0%, #ff9a9e 100%)"
            track-color="#f0f0f0"
            class="progress-bar"
          />
        </div>
        <div class="progress-sub">{{ progress }}%</div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, nextTick } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import api from '../api'

// 上传相关状态
const fileList = ref([])
const analyzing = ref(false)
const showProgress = ref(false)
const progress = ref(0)
const progressTip = ref('AI正在深度思考中...')
let progressTimer = null

// 结果相关状态
const showResult = ref(false)
const loading = ref(false)
const result = ref(null)
const analysisId = ref(null)
const activeNames = ref([]) // 数组，支持多个同时展开
const chatMessages = ref([])
const chatInput = ref('')
const chatMessagesRef = ref(null)

// 分析项配置
const analysisItems = computed(() => {
  if (!result.value) return []
  
  // 确保所有字段都有值，即使为空也显示"暂无数据"
  const getContent = (field) => {
    const value = result.value[field]
    if (value === null || value === undefined || value === '') {
      return '暂无数据'
    }
    return value
  }
  
  return [
    { name: 'personality', title: '性格分析', icon: 'user-o', content: getContent('personality') },
    { name: 'interests', title: '兴趣爱好', icon: 'star-o', content: getContent('interests') },
    { name: 'values', title: '价值观倾向', icon: 'like-o', content: getContent('values') },
    { name: 'emotion', title: '情感状态', icon: 'heart-o', content: getContent('emotion') },
    { name: 'income_analysis', title: '收入与消费能力', icon: 'gold-coin-o', content: getContent('income_analysis') },
    { name: 'communication', title: '沟通建议', icon: 'chat-o', content: formatCommunication(result.value.communication) || '暂无数据' },
    { name: 'relationship', title: '关系推进建议', icon: 'friends-o', content: getContent('relationship') },
    { name: 'warnings', title: '避雷指南', icon: 'warning-o', content: getContent('warnings') }
  ]
})

const toggleCard = (name) => {
  const index = activeNames.value.indexOf(name)
  if (index > -1) {
    activeNames.value.splice(index, 1)
  } else {
    activeNames.value.push(name)
  }
}

const formatCommunication = (comm) => {
  if (!comm || typeof comm === 'string') return comm || '暂无数据'
  let text = ''
  if (comm.topics && comm.topics.length > 0) {
    text += '推荐话题：\n' + comm.topics.map((t, i) => `${i + 1}. ${t}`).join('\n') + '\n\n'
  }
  if (comm.opening_lines && comm.opening_lines.length > 0) {
    text += '开场白建议：\n' + comm.opening_lines.map((l, i) => `${i + 1}. ${l}`).join('\n') + '\n\n'
  }
  if (comm.tips) {
    text += '聊天技巧：\n' + comm.tips
  }
  return text || '暂无数据'
}

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
  if (value === null || value === undefined) {
    return '暂无数据'
  }
  if (Array.isArray(value)) {
    return value.join('、')
  }
  if (typeof value === 'object') {
    // 如果是对象，尝试格式化为可读的文本
    // 如果是 communication 对象，使用 formatCommunication
    if (value.topics || value.opening_lines || value.tips) {
      return formatCommunication(value)
    }
    // 其他对象，转换为格式化的JSON字符串
    return JSON.stringify(value, null, 2)
  }
  if (typeof value === 'string' && value.trim() === '') {
    return '暂无数据'
  }
  return String(value) || '暂无数据'
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
    formData.append('supplementary_info', JSON.stringify({}))
    
    const response = await api.post('/analyses', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000
    })
    
    // 保存分析ID和结果
    analysisId.value = response.data.id
    let data = response.data.result
    
    // 如果 result 是字符串，尝试解析为JSON
    if (typeof data === 'string') {
      try {
        data = JSON.parse(data)
      } catch (e) {
        console.warn('解析结果失败，使用原始数据', e)
      }
    }
    
    // 如果 result 是数组，取第一个元素
    if (Array.isArray(data) && data.length > 0) {
      data = data[0]
    }
    
    // 确保 data 是对象
    if (typeof data !== 'object' || data === null) {
      data = {}
    }
    
    // 处理字符串字段：如果是对象或数组，转换为字符串
    const processField = (value) => {
      if (value === null || value === undefined) return '暂无数据'
      if (typeof value === 'string') return value
      if (typeof value === 'object') {
        // 如果是对象或数组，转换为格式化的JSON字符串
        return JSON.stringify(value, null, 2)
      }
      return String(value)
    }
    
    // 处理分析结果
    result.value = {
      match_score: data.match_score || 0,
      success_rate: data.success_rate || 0,
      personality: processField(data.personality),
      interests: processField(data.interests),
      values: processField(data.values),
      emotion: processField(data.emotion),
      income_analysis: processField(data.income_analysis),
      communication: (typeof data.communication === 'object' && data.communication !== null) 
        ? data.communication 
        : {
          topics: [],
          opening_lines: [],
          tips: '暂无数据'
        },
      relationship: processField(data.relationship),
      warnings: processField(data.warnings),
      summary: data.summary || ''
    }
    
    console.log('[DEBUG] 处理后的分析结果:', result.value)
    console.log('[DEBUG] 各字段长度检查:')
    console.log('  - personality:', result.value.personality?.length || 0)
    console.log('  - interests:', result.value.interests?.length || 0)
    console.log('  - values:', result.value.values?.length || 0)
    console.log('  - emotion:', result.value.emotion?.length || 0)
    console.log('  - income_analysis:', result.value.income_analysis?.length || 0)
    console.log('  - relationship:', result.value.relationship?.length || 0)
    console.log('  - warnings:', result.value.warnings?.length || 0)
    console.log('  - communication:', JSON.stringify(result.value.communication))
    
    // 显示结果
    showResult.value = true
    showToast({ type: 'success', message: '分析完成' })
    
    // 滚动到结果区域
    await nextTick()
    setTimeout(() => {
      const resultSection = document.querySelector('.result-section')
      if (resultSection) {
        resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 300)
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
  
  // 滚动到底部
  await nextTick()
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
  
  try {
    const response = await api.post(`/analyses/${analysisId.value}/chat`, {
      question
    })
    chatMessages.value.push({
      role: 'assistant',
      content: response.data.answer
    })
    
    // 滚动到底部
    await nextTick()
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
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
        // 用户取消分享
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
  showResult.value = false
  result.value = null
  analysisId.value = null
  chatMessages.value = []
  chatInput.value = ''
  activeNames.value = []
  
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onBeforeUnmount(() => {
  if (progressTimer) clearInterval(progressTimer)
})
</script>

<style scoped>
/* 全局样式 */
.home-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #ff9a9e 0%, #fecfef 50%, #f5f5f5 100%);
  padding: 0 16px 40px;
  position: relative;
}

/* 顶部标题 */
.header {
  padding: 50px 0 30px;
  text-align: center;
}

.header-content {
  animation: fadeInDown 0.6s ease-out;
}

.title {
  font-size: 36px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 12px;
  text-shadow: 0 2px 20px rgba(0, 0, 0, 0.15);
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 400;
}

/* 上传区域 */
.upload-section {
  max-width: 640px;
  margin: 0 auto 24px;
  animation: fadeInUp 0.6s ease-out 0.2s both;
}

.upload-section.has-result {
  margin-bottom: 32px;
}

.upload-card {
  background: #fff;
  border-radius: 24px;
  padding: 32px 24px;
  margin-bottom: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
}

.upload-card.uploaded {
  border-color: #07c160;
  box-shadow: 0 8px 32px rgba(7, 193, 96, 0.15);
}

.upload-empty {
  width: 100%;
}

.upload-slot {
  text-align: center;
  padding: 50px 20px;
}

.upload-icon-wrapper {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: all 0.3s ease;
}

.upload-slot:hover .upload-icon-wrapper {
  transform: scale(1.05);
  box-shadow: 0 8px 24px rgba(255, 154, 158, 0.3);
}

.upload-text {
  font-size: 16px;
  color: #333;
  font-weight: 500;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 13px;
  color: #999;
}

.upload-status {
  width: 100%;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.status-icon-wrapper {
  width: 32px;
  height: 32px;
  background: #07c160;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.status-text {
  flex: 1;
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.status-text strong {
  color: #07c160;
  font-weight: 600;
}

.reset-btn {
  font-size: 12px;
  padding: 4px 12px;
}

.upload-preview {
  margin-top: 12px;
}

.actions-wrapper {
  margin-top: 20px;
}

.analyze-btn {
  height: 52px;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(255, 107, 157, 0.3);
  transition: all 0.3s ease;
}

.analyze-btn:active {
  transform: scale(0.98);
}

.tip-text {
  margin-top: 12px;
  text-align: center;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

/* 结果区域 */
.result-section {
  max-width: 640px;
  margin: 0 auto;
}

.fade-slide-enter-active {
  animation: fadeSlideIn 0.5s ease-out;
}

.fade-slide-leave-active {
  animation: fadeSlideOut 0.3s ease-in;
}

/* 评分卡片 */
.score-card {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  border-radius: 20px;
  padding: 36px 32px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 8px 32px rgba(255, 154, 158, 0.25);
  animation: scaleIn 0.5s ease-out;
}

.score-item {
  text-align: center;
  flex: 1;
}

.score-value-wrapper {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  margin-bottom: 8px;
}

.score-value {
  font-size: 48px;
  font-weight: 700;
  color: #fff;
  line-height: 1;
}

.score-unit {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.score-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 500;
}

.score-divider {
  width: 1px;
  height: 60px;
  background: rgba(255, 255, 255, 0.3);
}

/* 分析卡片 */
.analysis-cards {
  margin-bottom: 20px;
}

.analysis-card {
  background: #fff;
  border-radius: 16px;
  margin-bottom: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #f0f0f0;
}

.analysis-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.analysis-card.expanded {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-header {
  padding: 18px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s ease;
}

.card-header:hover {
  background: #fafafa;
}

.card-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-icon {
  font-size: 20px;
  color: #ff6b9d;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.card-arrow {
  font-size: 16px;
  color: #999;
  transition: transform 0.3s ease;
}

.analysis-card.expanded .card-arrow {
  transform: rotate(180deg);
}

.card-content {
  padding: 0 20px 20px;
  border-top: 1px solid #f0f0f0;
}

.expand-enter-active {
  animation: expandDown 0.3s ease-out;
}

.expand-leave-active {
  animation: expandUp 0.3s ease-in;
}

.result-content-text {
  padding: 20px 0;
  line-height: 1.8;
  color: #666;
  white-space: pre-wrap;
  font-size: 14px;
}

/* 对话区域 */
.chat-section {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.chat-header .van-icon {
  font-size: 18px;
  color: #ff6b9d;
}

.chat-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.chat-messages {
  max-height: 320px;
  overflow-y: auto;
  margin-bottom: 16px;
  padding: 8px 0;
}

.chat-message {
  margin-bottom: 16px;
  animation: messageSlideIn 0.3s ease-out;
}

.chat-message.user {
  text-align: right;
}

.message-content {
  display: inline-block;
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 16px;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.5;
}

.chat-message:not(.user) .message-content {
  background: #f5f5f5;
  color: #333;
  border-top-left-radius: 4px;
}

.chat-message.user .message-content {
  background: linear-gradient(135deg, #ff6b9d 0%, #ff9a9e 100%);
  color: #fff;
  border-top-right-radius: 4px;
}

.chat-input-wrapper {
  margin-top: 12px;
}

.chat-field {
  border-radius: 24px;
  overflow: hidden;
}

/* 操作按钮 */
.result-actions {
  margin-top: 24px;
  padding: 0 4px;
}

.action-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.action-btn {
  flex: 1;
  height: 48px;
  font-weight: 500;
}

.action-btn.secondary {
  background: #fff;
  color: #333;
  border: 1px solid #e0e0e0;
}

.reset-analysis-btn {
  height: 48px;
  background: #f5f5f5;
  color: #666;
  border: none;
  font-weight: 500;
}

/* 进度弹窗 */
.progress-popup {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.progress-card {
  width: 340px;
  padding: 32px 24px;
  background: #fff;
  border-radius: 24px;
}

.progress-header {
  margin-bottom: 20px;
}

.hearts {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.heart {
  font-size: 28px;
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
  margin-bottom: 24px;
  font-size: 16px;
}

.progress-bar-wrapper {
  margin-bottom: 16px;
}

.progress-bar {
  border-radius: 10px;
  overflow: hidden;
}

.progress-sub {
  text-align: center;
  color: #999;
  font-size: 14px;
  font-weight: 500;
}

/* 动画 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeSlideOut {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-30px);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes expandDown {
  from {
    opacity: 0;
    max-height: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    max-height: 500px;
    transform: translateY(0);
  }
}

@keyframes expandUp {
  from {
    opacity: 1;
    max-height: 500px;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    max-height: 0;
    transform: translateY(-10px);
  }
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.8;
  }
}

.card-fade-enter-active {
  animation: cardFadeIn 0.4s ease-out;
}

.message-fade-enter-active {
  animation: messageSlideIn 0.3s ease-out;
}
</style>
