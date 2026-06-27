import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

describe('useTheme', () => {
  let setAttributeMock: ReturnType<typeof vi.fn>
  let originalSetAttribute: typeof Element.prototype.setAttribute

  beforeEach(async () => {
    localStorage.clear()
    vi.resetModules()

    setAttributeMock = vi.fn()
    originalSetAttribute = document.documentElement.setAttribute
    document.documentElement.setAttribute = setAttributeMock as any
  })

  afterEach(() => {
    document.documentElement.setAttribute = originalSetAttribute
  })

  it('init() applies light theme when nothing is stored', async () => {
    const { useTheme } = await import('@/composables/useTheme')
    const { init } = useTheme()
    init()
    expect(setAttributeMock).toHaveBeenCalledWith('data-theme', 'light')
  })

  it('init() applies dark theme when localStorage has "dark"', async () => {
    localStorage.setItem('codeseer-theme', 'dark')
    const { useTheme } = await import('@/composables/useTheme')
    const { isDark, init } = useTheme()
    init()
    expect(isDark.value).toBe(true)
    expect(setAttributeMock).toHaveBeenCalledWith('data-theme', 'dark')
  })

  it('toggle() flips isDark from false to true', async () => {
    const { useTheme } = await import('@/composables/useTheme')
    const { isDark, init, toggle } = useTheme()
    init()
    expect(isDark.value).toBe(false)
    toggle()
    expect(isDark.value).toBe(true)
  })
})
