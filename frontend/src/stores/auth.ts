import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/index'

export interface AuthUser {
  id: string
  email: string
  name: string
  role: string
  avatar_color?: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<AuthUser | null>(null)

  const isLoggedIn = computed(() => !!token.value && !!user.value)

  async function login(email: string, password: string) {
    const res = await authApi.login({ email, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('auth_token', res.data.access_token)
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('auth_token')
  }

  async function initFromStorage() {
    const stored = localStorage.getItem('auth_token')
    if (!stored) return
    token.value = stored
    try {
      const res = await authApi.me()
      user.value = res.data
    } catch {
      token.value = null
      user.value = null
      localStorage.removeItem('auth_token')
    }
  }

  return { token, user, isLoggedIn, login, logout, initFromStorage }
})
