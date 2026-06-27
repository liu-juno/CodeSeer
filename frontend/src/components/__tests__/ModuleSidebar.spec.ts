import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import ModuleSidebar from '../ModuleSidebar.vue'

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/:pathMatch(.*)*', component: { template: '<div />' } }]
})

describe('ModuleSidebar', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders all nav groups', () => {
    const wrapper = mount(ModuleSidebar, {
      global: {
        plugins: [router],
        stubs: { ElIcon: true, ElTooltip: { template: '<slot />' } }
      }
    })
    const links = wrapper.findAll('.nav-item')
    expect(links.length).toBeGreaterThanOrEqual(8)
  })

  it('renders two dividers separating three groups', () => {
    const wrapper = mount(ModuleSidebar, {
      global: {
        plugins: [router],
        stubs: { ElIcon: true, ElTooltip: { template: '<slot />' } }
      }
    })
    expect(wrapper.findAll('.nav-divider')).toHaveLength(2)
  })
})
