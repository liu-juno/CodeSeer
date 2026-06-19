import { ref } from 'vue'
import { mcpTokensApi } from '@/api/index'

export interface TokenItem {
  id: string
  name: string
  prefix: string
  expires_at: string | null
  last_used_at?: string | null
  created_at: string
}

export function useTokenManager(userId: string) {
  const tokens = ref<TokenItem[]>([])

  async function fetchTokens() {
    const res = await mcpTokensApi.list(userId)
    tokens.value = res.data.tokens
  }

  async function createToken(payload: { name: string; user_id: string; days?: number }) {
    const res = await mcpTokensApi.create(payload)
    await fetchTokens()
    return res.data
  }

  async function revokeToken(tokenId: string) {
    await mcpTokensApi.delete(tokenId, userId)
    await fetchTokens()
  }

  return { tokens, fetchTokens, createToken, revokeToken }
}
