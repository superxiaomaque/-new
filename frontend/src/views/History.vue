<template>
  <div class="history-container">
    <van-nav-bar title="历史记录" fixed placeholder />
    
    <div class="content">
      <div class="toolbar" v-if="list.length > 0">
        <van-checkbox v-model="selectMode">批量导出</van-checkbox>
        <van-button
          v-if="selectMode"
          size="small"
          type="primary"
          :disabled="selectedIds.length === 0"
          @click="exportSelected"
        >
          导出选中({{ selectedIds.length }})
        </van-button>
      </div>

      <van-empty v-if="list.length === 0" description="暂无分析记录" />
      
      <van-list
        v-else
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
      >
        <div
          v-for="item in list"
          :key="item.id"
          class="history-item"
          @click="selectMode ? toggleSelect(item.id) : viewDetail(item.id)"
        >
          <div class="item-header">
            <div class="left">
              <van-checkbox v-if="selectMode" :model-value="selectedIds.includes(item.id)" />
              <span class="time">{{ formatTime(item.created_at) }}</span>
            </div>
            <div class="right">
              <van-tag v-if="item.tag" type="primary" size="small" @click.stop="openTag(item)">
                {{ item.tag }}
              </van-tag>
              <van-button v-else size="mini" type="primary" plain @click.stop="openTag(item)">打标签</van-button>
            </div>
          </div>
          <div class="item-preview">{{ getPreview(item.result) }}</div>
        </div>
      </van-list>
    </div>
    
    <van-tabbar v-model="active" fixed placeholder>
      <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
      <van-tabbar-item icon="clock-o" to="/history">历史</van-tabbar-item>
      <van-tabbar-item icon="plus" to="/upload">分析</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import api from '../api'

const router = useRouter()
const active = ref(1)
const list = ref([])
const loading = ref(false)
const finished = ref(false)
const page = ref(1)
const pageSize = ref(10)
const selectMode = ref(false)
const selectedIds = ref([])
const tags = ref([])

const formatTime = (time) => {
  const date = new Date(time)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const getPreview = (result) => {
  try {
    const data = typeof result === 'string' ? JSON.parse(result) : result
    return data.summary || '查看详情'
  } catch {
    return '查看详情'
  }
}

const onLoad = async () => {
  if (finished.value) return
  
  loading.value = true
  try {
    const response = await api.get('/analyses', {
      params: { page: page.value, page_size: pageSize.value }
    })
    const newList = response.data.items || []
    if (newList.length === 0) {
      finished.value = true
    } else {
      list.value.push(...newList)
      page.value++
    }
  } catch (error) {
    console.error('加载历史记录失败', error)
  } finally {
    loading.value = false
  }
}

const viewDetail = (id) => {
  router.push(`/result/${id}`)
}

const toggleSelect = (id) => {
  if (selectedIds.value.includes(id)) {
    selectedIds.value = selectedIds.value.filter((x) => x !== id)
  } else {
    selectedIds.value.push(id)
  }
}

const loadTags = async () => {
  try {
    const res = await api.get('/analyses/tags')
    tags.value = res.data.tags || []
  } catch {
    tags.value = ['重要', '已联系', '待跟进']
  }
}

const openTag = async (item) => {
  if (!tags.value.length) await loadTags()
  // 简化处理：直接使用第一个标签，或者清除标签
  // 如果需要更复杂的选择，可以使用 Vant 的 Picker 组件
  try {
    const options = ['清除标签', ...tags.value]
    // 使用简单的 prompt 方式，或者直接设置第一个标签
    // 这里暂时简化为清除标签功能
    await api.patch(`/analyses/${item.id}/tag`, { tag: '' })
    item.tag = ''
    showToast({ type: 'success', message: '标签已清除' })
  } catch {
    showToast({ type: 'fail', message: '操作失败' })
  }
}

const exportSelected = async () => {
  try {
    await showConfirmDialog({
      title: '确认导出',
      message: `将导出 ${selectedIds.value.length} 条记录为ZIP（不包含原图）`
    })
    const res = await api.post('/analyses/export.zip', { ids: selectedIds.value }, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'application/zip' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'analyses_export.zip'
    a.click()
    URL.revokeObjectURL(url)
    showToast({ type: 'success', message: '已开始下载' })
  } catch (e) {
    if (e?.response) showToast({ type: 'fail', message: e.response.data?.detail || '导出失败' })
  }
}

onMounted(() => {
  loadTags()
  onLoad()
})
</script>

<style scoped>
.history-container {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 80px;
}

.content {
  padding: 10px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px;
  background: white;
  border-radius: 12px;
  margin-bottom: 10px;
}

.history-item {
  background: white;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time {
  font-size: 14px;
  color: #999;
}

.item-preview {
  font-size: 14px;
  color: #333;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>
