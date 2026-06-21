import { describe, it, expect, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

describe('Projects pagination', () => {
  it('should render pagination component after data loads', async () => {
    const mockResponse = {
      items: [{ id: '1', name: 'Test Project', identifier: 'test', status: 'active' }],
      total: 1,
      page: 1,
      page_size: 20,
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    })

    const { mount } = await import('@vue/test-utils')
    const Projects = (await import('@/views/Projects.vue')).default

    const wrapper = mount(Projects, {
      global: {
        stubs: {
          'el-table': { template: '<div class="el-table-stub"></div>' },
          'el-pagination': { template: '<div class="el-pagination-stub"></div>' },
          'el-button': { template: '<button><slot /></button>' },
          'el-input': { template: '<input />' },
          'el-dialog': { template: '<div class="el-dialog-stub"></div>' },
          'el-form': { template: '<form><slot /></form>' },
          'el-form-item': { template: '<div class="el-form-item-stub"><slot /></div>' },
          'el-select': { template: '<select><slot /></select>' },
          'el-option': { template: '<option><slot /></option>' },
          'el-table-column': { template: '<div class="el-table-column-stub"></div>' },
          'el-link': { template: '<a><slot /></a>' },
          'el-tag': { template: '<span><slot /></span>' },
          'el-text': { template: '<span><slot /></span>' },
          'el-icon': { template: '<span class="el-icon-stub"></span>' },
          'el-step': { template: '<div class="el-step-stub"></div>' },
          'el-steps': { template: '<div class="el-steps-stub"></div>' },
          'el-radio-button': { template: '<div class="el-radio-button-stub"></div>' },
          'el-radio-group': { template: '<div class="el-radio-group-stub"></div>' },
          'el-date-picker': { template: '<input type="date" />' },
          Plus: { template: '<span class="icon-plus">+</span>' },
        },
      },
    })

    await flushPromises()

    const pagination = wrapper.find('.el-pagination-stub, [class*="pagination"]')
    expect(pagination.exists()).toBe(true)
  })
})
