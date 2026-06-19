import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/index', () => ({
  default: {},
  authApi: {
    login: vi.fn(),
    me: vi.fn(),
  },
}))

import { authApi } from '@/api/index'
import { useAuthStore } from '@/stores/auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.resetAllMocks()
    localStorage.clear()
  })

  it('初始状态：未登录', () => {
    const store = useAuthStore()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(store.isLoggedIn).toBe(false)
  })

  it('login 成功后保存 token 和 user', async () => {
    ;(authApi.login as any).mockResolvedValue({
      data: {
        access_token: 'jwt-abc',
        token_type: 'bearer',
        user: { id: 'u1', email: 'dev@cs.io', name: 'Dev', role: 'developer' },
      },
    })
    const store = useAuthStore()
    await store.login('dev@cs.io', 'secret')
    expect(store.token).toBe('jwt-abc')
    expect(store.user?.email).toBe('dev@cs.io')
    expect(store.isLoggedIn).toBe(true)
  })

  it('login 成功后 token 写入 localStorage', async () => {
    ;(authApi.login as any).mockResolvedValue({
      data: {
        access_token: 'jwt-abc',
        token_type: 'bearer',
        user: { id: 'u1', email: 'dev@cs.io', name: 'Dev', role: 'developer' },
      },
    })
    const store = useAuthStore()
    await store.login('dev@cs.io', 'secret')
    expect(localStorage.getItem('auth_token')).toBe('jwt-abc')
  })

  it('login 失败时抛出错误', async () => {
    ;(authApi.login as any).mockRejectedValue(new Error('401'))
    const store = useAuthStore()
    await expect(store.login('bad@cs.io', 'wrong')).rejects.toThrow()
    expect(store.isLoggedIn).toBe(false)
  })

  it('logout 清除 token 和 user', async () => {
    ;(authApi.login as any).mockResolvedValue({
      data: {
        access_token: 'jwt-abc',
        token_type: 'bearer',
        user: { id: 'u1', email: 'dev@cs.io', name: 'Dev', role: 'developer' },
      },
    })
    const store = useAuthStore()
    await store.login('dev@cs.io', 'secret')
    store.logout()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(store.isLoggedIn).toBe(false)
    expect(localStorage.getItem('auth_token')).toBeNull()
  })

  it('initFromStorage 从 localStorage 恢复 token', async () => {
    localStorage.setItem('auth_token', 'stored-jwt')
    ;(authApi.me as any).mockResolvedValue({
      data: { id: 'u1', email: 'dev@cs.io', name: 'Dev', role: 'developer' },
    })
    const store = useAuthStore()
    await store.initFromStorage()
    expect(store.token).toBe('stored-jwt')
    expect(store.user?.email).toBe('dev@cs.io')
  })

  it('initFromStorage: me 接口失败时清除 token', async () => {
    localStorage.setItem('auth_token', 'expired-jwt')
    ;(authApi.me as any).mockRejectedValue(new Error('401'))
    const store = useAuthStore()
    await store.initFromStorage()
    expect(store.token).toBeNull()
    expect(localStorage.getItem('auth_token')).toBeNull()
  })
})
