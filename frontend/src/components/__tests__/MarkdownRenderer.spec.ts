import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MarkdownRenderer from '../MarkdownRenderer.vue'

vi.mock('marked', () => ({
  marked: (content: string) => `<h1>Test</h1><p>${content}</p>`
}))

describe('MarkdownRenderer', () => {
  it('should render markdown content', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: { content: '# Hello\n\nThis is **bold** text' }
    })
    expect(wrapper.find('.markdown-body').exists()).toBe(true)
  })

  it('should show preview tab by default', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: { content: '# Test' }
    })
    expect(wrapper.find('.markdown-body').isVisible()).toBe(true)
  })

  it('should render source code in source tab', async () => {
    const wrapper = mount(MarkdownRenderer, {
      props: { content: '# Test Content' }
    })
    await wrapper.findAll('.el-tabs__item').at(1)?.trigger('click')
    expect(wrapper.find('.source-code').text()).toBe('# Test Content')
  })
})