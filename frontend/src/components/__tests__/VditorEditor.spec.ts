import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import VditorEditor from '../VditorEditor.vue'

vi.mock('vditor', () => {
  return {
    default: class MockVditor {
      constructor() {}
      getValue = () => ''
      setValue = vi.fn()
      getElement = () => ({ addEventListener: vi.fn() })
      destroy = vi.fn()
    }
  }
})

describe('VditorEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render editor container', () => {
    const wrapper = mount(VditorEditor, {
      props: { modelValue: '# Hello Markdown' }
    })
    expect(wrapper.find('.vditor-editor').exists()).toBe(true)
  })

  it('should emit update:modelValue when handleValueChanged is called', () => {
    const wrapper = mount(VditorEditor, {
      props: { modelValue: '' }
    })
    const vm = wrapper.vm as any
    vm.handleValueChanged('# New Content')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['# New Content'])
  })
})