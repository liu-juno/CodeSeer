import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectsApi } from '@/api'

export const useProjectStore = defineStore('project', () => {
  const currentProjectId = ref<string | null>(null)
  const currentProject = ref<any | null>(null)
  const myProjects = ref<any[]>([])
  const currentIterationId = ref<string | null>(null)
  const currentIteration = ref<any | null>(null)

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

  function setCurrentIteration(iteration: any | null) {
    currentIteration.value = iteration
    currentIterationId.value = iteration?.id ?? null
    if (iteration?.id) {
      localStorage.setItem('currentIterationId', iteration.id)
    } else {
      localStorage.removeItem('currentIterationId')
    }
  }

  function clearCurrentIteration() {
    currentIteration.value = null
    currentIterationId.value = null
    localStorage.removeItem('currentIterationId')
  }

  async function fetchMyProjects() {
    const res = await projectsApi.getMine()
    myProjects.value = res.data
    return myProjects.value
  }

  function initFromStorage() {
    const storedProject = localStorage.getItem('currentProjectId')
    if (storedProject) currentProjectId.value = storedProject

    const storedIteration = localStorage.getItem('currentIterationId')
    if (storedIteration) currentIterationId.value = storedIteration
  }

  return {
    currentProjectId,
    currentProject,
    myProjects,
    currentIterationId,
    currentIteration,
    hasProject,
    setCurrentProject,
    clearCurrentProject,
    setCurrentIteration,
    clearCurrentIteration,
    fetchMyProjects,
    initFromStorage
  }
})
