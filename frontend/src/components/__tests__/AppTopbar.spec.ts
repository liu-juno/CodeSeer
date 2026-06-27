import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import AppTopbar from '../AppTopbar.vue'

vi.mock('@/api', () => ({
  iterationsApi: { byProject: vi.fn().mockResolvedValue({ data: [] }) }
}))
vi.mock('@/composables/useTheme', () => ({
  useTheme: () => ({ isDark: { value: false }, toggle: vi.fn(), init: vi.fn() })
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/:pathMatch(.*)*', component: { template: '<div />' } }]
})

const elStubs = {
  ElDropdown: { template: '<div><slot /><slot name="dropdown" /></div>' },
  ElDropdownMenu: { template: '<div><slot /></div>' },
  ElDropdownItem: { template: '<div><slot /></div>' },
  ElIcon: true,
}

describe('AppTopbar', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders the user avatar initial', async () => {
    const { useAuthStore } = await import('@/stores/auth')
    const auth = useAuthStore()
    auth.user = { name: 'Test User' } as any
    const wrapper = mount(AppTopbar, { global: { plugins: [router], stubs: elStubs } })
    expect(wrapper.find('.user-avatar').text()).toBe('T')
  })

  it('shows "选择迭代" placeholder when no iteration is selected', () => {
    const wrapper = mount(AppTopbar, { global: { plugins: [router], stubs: elStubs } })
    expect(wrapper.find('.iteration-label').text()).toBe('选择迭代')
  })

  it('shows current iteration name when one is selected', async () => {
    const { useProjectStore } = await import('@/stores/project')
    const store = useProjectStore()
    store.currentIteration = { id: 'it-1', name: 'Sprint 3' }
    const wrapper = mount(AppTopbar, { global: { plugins: [router], stubs: elStubs } })
    expect(wrapper.find('.iteration-label').text()).toBe('Sprint 3')
  })
})
