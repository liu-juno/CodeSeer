import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ProjectRail from '../ProjectRail.vue'

const projects = [
  { id: '1', name: 'Alpha' },
  { id: '2', name: 'Beta' },
]
const stubs = { ElTooltip: { template: '<slot />' } }

describe('ProjectRail', () => {
  it('renders one icon per project', () => {
    const wrapper = mount(ProjectRail, {
      props: { projects, currentProjectId: '1' },
      global: { stubs }
    })
    expect(wrapper.findAll('.project-icon')).toHaveLength(2)
  })

  it('first letter of project name appears in each icon', () => {
    const wrapper = mount(ProjectRail, {
      props: { projects, currentProjectId: null },
      global: { stubs }
    })
    const icons = wrapper.findAll('.project-icon')
    expect(icons[0].text()).toBe('A')
    expect(icons[1].text()).toBe('B')
  })

  it('active project icon has .active class', () => {
    const wrapper = mount(ProjectRail, {
      props: { projects, currentProjectId: '1' },
      global: { stubs }
    })
    const icons = wrapper.findAll('.project-icon')
    expect(icons[0].classes()).toContain('active')
    expect(icons[1].classes()).not.toContain('active')
  })

  it('emits select-project with the project when icon is clicked', async () => {
    const wrapper = mount(ProjectRail, {
      props: { projects, currentProjectId: null },
      global: { stubs }
    })
    await wrapper.findAll('.project-icon')[1].trigger('click')
    expect(wrapper.emitted('select-project')?.[0]).toEqual([projects[1]])
  })

  it('emits create-project when + button is clicked', async () => {
    const wrapper = mount(ProjectRail, {
      props: { projects, currentProjectId: null },
      global: { stubs }
    })
    await wrapper.find('.create-btn').trigger('click')
    expect(wrapper.emitted('create-project')).toBeTruthy()
  })
})
