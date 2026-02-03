<template>
  <div class="share-container">
    <van-nav-bar title="分享的分析结果" fixed placeholder />

    <div v-if="loading" class="loading-container">
      <van-loading type="spinner" size="24px">加载中...</van-loading>
    </div>

    <div v-else-if="data" class="content">
      <div class="notice">
        <van-notice-bar
          left-icon="info-o"
          text="该分享链接不包含原始截图，仅展示分析结果。"
        />
      </div>

      <div class="score-card">
        <div class="score-item">
          <div class="score-value">{{ data.result.match_score || 0 }}</div>
          <div class="score-label">匹配度</div>
        </div>
        <div class="score-item">
          <div class="score-value">{{ data.result.success_rate || 0 }}%</div>
          <div class="score-label">脱单成功率</div>
        </div>
      </div>

      <van-collapse v-model="activeNames" accordion>
        <van-collapse-item title="性格分析" name="personality">
          <div class="result-content">{{ data.result.personality || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="兴趣爱好" name="interests">
          <div class="result-content">{{ data.result.interests || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="价值观倾向" name="values">
          <div class="result-content">{{ data.result.values || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="情感状态" name="emotion">
          <div class="result-content">{{ data.result.emotion || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="沟通建议" name="communication">
          <div class="result-content">
            <div v-if="data.result.communication?.topics?.length">
              <h4>推荐话题：</h4>
              <ul>
                <li v-for="(t, i) in data.result.communication.topics" :key="i">{{ t }}</li>
              </ul>
            </div>
            <div v-if="data.result.communication?.opening_lines?.length">
              <h4>开场白建议：</h4>
              <ul>
                <li v-for="(t, i) in data.result.communication.opening_lines" :key="i">{{ t }}</li>
              </ul>
            </div>
            <div v-if="data.result.communication?.tips">
              <h4>聊天技巧：</h4>
              <p>{{ data.result.communication.tips }}</p>
            </div>
          </div>
        </van-collapse-item>
        <van-collapse-item title="关系推进建议" name="relationship">
          <div class="result-content">{{ data.result.relationship || '暂无数据' }}</div>
        </van-collapse-item>
        <van-collapse-item title="避雷指南" name="warnings">
          <div class="result-content">{{ data.result.warnings || '暂无数据' }}</div>
        </van-collapse-item>
      </van-collapse>

      <div class="meta">
        <div>已被查看：{{ data.view_count }} 次</div>
      </div>
    </div>

    <van-empty v-else description="链接不存在或已过期" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import api from '../api'

const route = useRoute()
const token = route.params.token

const loading = ref(true)
const data = ref(null)
const activeNames = ref('personality')

const load = async () => {
  try {
    const res = await api.get(`/shares/${token}`)
    data.value = res.data
  } catch (e) {
    showToast({ type: 'fail', message: e?.response?.data?.detail || '加载失败' })
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.share-container {
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
  margin: 10px 0;
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

.meta {
  margin-top: 10px;
  padding: 10px 12px;
  color: #999;
  font-size: 12px;
}
</style>

