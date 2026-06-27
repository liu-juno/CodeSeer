import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectsApi } from '@/api'

export const useProjectStore = defineStore('project', () => {
  const currentProjectId = ref<string | null>(null)
  const currentProject = ref<any | null>(null)
  const myProjects = ref<any[]>([])

  const hasProject = computed(() => !!currentProjectId.value)

  function setCurrentProject(project: any) {
    currentProject.value = project
    currentProjectId.value = project.id
    localStorage.setItem('currentProjectId', project.id)
  }

  function clearCurrentProject() {
    currentProject.value = null
    currentProjectId.value = null
    localStorage.removeItem('currentProjectId')
  }

  async function fetchMyProjects() {
    const res = await projectsApi.getMine()
    myProjects.value = res.data
    return myProjects.value
  }

  function initFromStorage() {
    const stored = localStorage.getItem('currentProjectId')
    if (stored) {
      currentProjectId.value = stored
    }
  }

  return {
    currentProjectId,
    currentProject,
    myProjects,
    hasProject,
    setCurrentProject,
    clearCurrentProject,
    fetchMyProjects,
    initFromStorage
  }
})
