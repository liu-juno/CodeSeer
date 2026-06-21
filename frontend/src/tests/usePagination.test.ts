import { describe, it, expect, vi } from 'vitest'

const mockFetcher = vi.fn().mockResolvedValue({ items: [], total: 0 })

describe('usePagination', () => {
  it('should initialize with correct defaults', async () => {
    const { usePagination } = await import('@/composables/usePagination')
    const { page, pageSize, total } = usePagination(mockFetcher)

    expect(page.value).toBe(1)
    expect(pageSize.value).toBe(20)
    expect(total.value).toBe(0)
  })

  it('should return required properties', async () => {
    const { usePagination } = await import('@/composables/usePagination')
    const result = usePagination(mockFetcher)

    expect(result).toHaveProperty('items')
    expect(result).toHaveProperty('total')
    expect(result).toHaveProperty('page')
    expect(result).toHaveProperty('pageSize')
    expect(result).toHaveProperty('loading')
    expect(result).toHaveProperty('fetchPage')
    expect(result).toHaveProperty('onPageChange')
    expect(result).toHaveProperty('onSizeChange')
  })
})
