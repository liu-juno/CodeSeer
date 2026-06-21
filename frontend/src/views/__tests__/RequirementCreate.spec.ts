import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'

vi.mock('@/api', () => ({
  requirementsApi: {
    create: vi.fn().mockResolvedValue({ data: { id: 'test-id' } })
  },
  attachmentsApi: {
    upload: vi.fn().mockResolvedValue({ data: {} })
  },
  iterationsApi: { list: vi.fn().mockResolvedValue({ data: { items: [] } }) },
  projectsApi: { list: vi.fn().mockResolvedValue({ data: { items: [] } }) },
}))

vi.mock('vditor', () => ({
  default: class MockVditor {
    constructor() {}
    getValue = () => ''
    setValue = vi.fn()
    getElement = () => ({ addEventListener: vi.fn() })
    destroy = vi.fn()
  }
}))

describe('RequirementCreate', () => {
  it('should render create page with title', async () => {
    const RequirementCreate = await import('../RequirementCreate.vue')
    const router = createRouter({
      history: createWebHistory(),
      routes: [{ path: '/requirement/new', component: () => Promise.resolve(RequirementCreate.default) }]
    })
    router.push('/requirement/new')
    await router.isReady()
    const wrapper = mount(RequirementCreate.default, {
      global: { plugins: [router] }
    })
    expect(wrapper.find('.page-title').text()).toBe('创建需求')
  })
})