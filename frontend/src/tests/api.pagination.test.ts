import { describe, it, expect } from 'vitest'

describe('API pagination smoke test', () => {
  it('API files should have no syntax errors', async () => {
    const { default: api } = await import('@/api')
    expect(api).toBeDefined()
    expect(api.get).toBeDefined()
  })
})
