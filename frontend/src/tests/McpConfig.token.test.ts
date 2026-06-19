/**
 * TDD tests for Token Management UI in McpConfig.vue
 * Written BEFORE production code.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/index', () => ({
  mcpTokensApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn().mockResolvedValue({}),
  },
}))

import { mcpTokensApi } from '@/api/index'
import { useTokenManager } from '@/composables/useTokenManager'

describe('useTokenManager composable', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns tokens ref and fetchTokens/createToken/revokeToken', () => {
    ;(mcpTokensApi.list as any).mockResolvedValue({ data: { tokens: [] } })
    const result = useTokenManager('user-001')
    expect(result).toHaveProperty('tokens')
    expect(result).toHaveProperty('fetchTokens')
    expect(result).toHaveProperty('createToken')
    expect(result).toHaveProperty('revokeToken')
  })

  it('fetchTokens populates tokens list from API', async () => {
    ;(mcpTokensApi.list as any).mockResolvedValue({
      data: {
        tokens: [
          { id: 't1', name: 'CI Token', prefix: 'codeseer_ab', created_at: '2026-06-19T00:00:00Z', expires_at: null },
        ],
      },
    })
    const { tokens, fetchTokens } = useTokenManager('user-001')
    await fetchTokens()
    expect(tokens.value).toHaveLength(1)
    expect(tokens.value[0].name).toBe('CI Token')
    expect(mcpTokensApi.list).toHaveBeenCalledWith('user-001')
  })

  it('createToken calls API and returns plain token string', async () => {
    ;(mcpTokensApi.create as any).mockResolvedValue({
      data: { token_id: 'new-id', token: 'codeseer_abc123', prefix: 'codeseer_abc', name: 'New Token', expires_at: null, created_at: '2026-06-19T00:00:00Z' },
    })
    ;(mcpTokensApi.list as any).mockResolvedValue({ data: { tokens: [] } })

    const { createToken } = useTokenManager('user-001')
    const result = await createToken({ name: 'New Token', user_id: 'user-001' })
    expect(result.token).toBe('codeseer_abc123')
    expect(mcpTokensApi.create).toHaveBeenCalledWith({ name: 'New Token', user_id: 'user-001' })
  })

  it('createToken refreshes token list after creation', async () => {
    ;(mcpTokensApi.create as any).mockResolvedValue({
      data: { token_id: 'new-id', token: 'codeseer_abc123', prefix: 'codeseer_abc', name: 'T', expires_at: null, created_at: '2026-06-19T00:00:00Z' },
    })
    ;(mcpTokensApi.list as any).mockResolvedValue({
      data: { tokens: [{ id: 'new-id', name: 'T', prefix: 'codeseer_abc', created_at: '2026-06-19T00:00:00Z', expires_at: null }] },
    })
    const { tokens, createToken } = useTokenManager('user-001')
    await createToken({ name: 'T', user_id: 'user-001' })
    expect(tokens.value).toHaveLength(1)
  })

  it('revokeToken calls delete API and refreshes list', async () => {
    ;(mcpTokensApi.list as any)
      .mockResolvedValueOnce({ data: { tokens: [{ id: 't1', name: 'CI', prefix: 'codeseer_ab', created_at: '2026-06-19T00:00:00Z', expires_at: null }] } })
      .mockResolvedValueOnce({ data: { tokens: [] } })
    ;(mcpTokensApi.delete as any).mockResolvedValue({})

    const { tokens, fetchTokens, revokeToken } = useTokenManager('user-001')
    await fetchTokens()
    expect(tokens.value).toHaveLength(1)

    await revokeToken('t1')
    expect(mcpTokensApi.delete).toHaveBeenCalledWith('t1', 'user-001')
    expect(tokens.value).toHaveLength(0)
  })
})

describe('McpConfig.vue Token UI', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    setActivePinia(createPinia())
  })

  it('renders Access Token section heading', async () => {
    ;(mcpTokensApi.list as any).mockResolvedValue({ data: { tokens: [] } })
    const McpConfig = (await import('@/views/McpConfig.vue')).default
    const wrapper = mount(McpConfig, { global: { plugins: [createPinia()], stubs: { RouterLink: true } } })
    await flushPromises()
    expect(wrapper.text()).toContain('Access Token')
  })

  it('renders 申请新 Token button', async () => {
    ;(mcpTokensApi.list as any).mockResolvedValue({ data: { tokens: [] } })
    const McpConfig = (await import('@/views/McpConfig.vue')).default
    const wrapper = mount(McpConfig, { global: { plugins: [createPinia()], stubs: { RouterLink: true } } })
    await flushPromises()
    expect(wrapper.text()).toContain('申请新 Token')
  })

  it('shows token name and prefix in list after fetch', async () => {
    ;(mcpTokensApi.list as any).mockResolvedValue({
      data: { tokens: [{ id: 't1', name: 'Deploy', prefix: 'codeseer_de', created_at: '2026-06-19T00:00:00Z', expires_at: null }] },
    })
    const McpConfig = (await import('@/views/McpConfig.vue')).default
    const wrapper = mount(McpConfig, { global: { plugins: [createPinia()], stubs: { RouterLink: true } } })
    await flushPromises()
    expect(wrapper.text()).toContain('Deploy')
    expect(wrapper.text()).toContain('codeseer_de')
  })
})
