import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
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
