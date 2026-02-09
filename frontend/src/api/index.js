import axios from 'axios'

// 根据环境变量决定 API 地址
// 开发环境使用代理，生产环境使用环境变量或默认值
const getBaseURL = () => {
  // 如果设置了环境变量，使用环境变量
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  // 开发环境使用相对路径（会被 vite proxy 处理）
  if (import.meta.env.DEV) {
    return '/api'
  }
  // 生产环境默认使用相对路径（需要配置反向代理或使用完整 URL）
  return '/api'
}

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 300000  // 增加到5分钟，因为分析可能需要较长时间
})

// 请求拦截器 - 添加调试日志
api.interceptors.request.use(
  (config) => {
    console.log('[API Request]', config.method?.toUpperCase(), config.url, config)
    return config
  },
  (error) => {
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('[API Response]', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('[API Error]', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message
    })
    return Promise.reject(error)
  }
)

export default api
