import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)

  const isLoggedIn = computed(() => {
    return !!token.value
  })

  const login = async (phone, password) => {
    return { success: false, message: '已启用匿名模式，无需登录' }
  }

  const register = async (phone, password) => {
    return { success: false, message: '已关闭注册，请直接登录（首次登录会自动创建账号）' }
  }

  const forgotPassword = async (phone, newPassword) => {
    return { success: false, message: '已启用匿名模式，无需找回密码' }
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    login,
    register,
    forgotPassword,
    logout
  }
})
