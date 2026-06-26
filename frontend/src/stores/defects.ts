import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { defectsApi } from '@/api'

export const useDefectsStore = defineStore('defects', () => {
  const defects = ref<any[]>([])
  const currentDefect = ref<any>(null)
  const loading = ref(false)
  const filters = ref({
    project_id: null,
    status: null,
    severity: null,
    priority: null,
    assignee: null,
    creator_id: null,
    module_id: null,
    requirement_id: null,
  })

  const byStatus = computed(() => {
    const groups: Record<string, any[]> = {}
    for (const d of defects.value) {
      const key = d.status
      if (!groups[key]) groups[key] = []
      groups[key].push(d)
    }
    return groups
  })

  const byPriority = computed(() => {
    const groups: Record<string, any[]> = {}
    for (const d of defects.value) {
      const key = d.priority
      if (!groups[key]) groups[key] = []
      groups[key].push(d)
    }
    return groups
  })

  const bySeverity = computed(() => {
    const groups: Record<string, any[]> = {}
    for (const d of defects.value) {
      const key = d.severity
      if (!groups[key]) groups[key] = []
      groups[key].push(d)
    }
    return groups
  })

  const fetchList = async () => {
    loading.value = true
    try {
      const res = await defectsApi.list(filters.value)
      defects.value = res.data
    } finally {
      loading.value = false
    }
  }

  const fetchOne = async (id: string) => {
    loading.value = true
    try {
      const res = await defectsApi.get(id)
      currentDefect.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  return {
    defects, currentDefect, loading, filters,
    byStatus, byPriority, bySeverity,
    fetchList, fetchOne
  }
})