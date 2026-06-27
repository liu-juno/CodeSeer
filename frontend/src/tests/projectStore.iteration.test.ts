import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProjectStore } from '@/stores/project'

describe('projectStore — iteration context', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('currentIterationId is null by default', () => {
    const store = useProjectStore()
    expect(store.currentIterationId).toBeNull()
  })

  it('setCurrentIteration() sets the iteration and persists id', () => {
    const store = useProjectStore()
    store.setCurrentIteration({ id: 'it-1', name: 'Sprint 1' })
    expect(store.currentIterationId).toBe('it-1')
    expect(store.currentIteration?.name).toBe('Sprint 1')
    expect(localStorage.getItem('currentIterationId')).toBe('it-1')
  })

  it('setCurrentIteration(null) clears the iteration', () => {
    const store = useProjectStore()
    store.setCurrentIteration({ id: 'it-1', name: 'Sprint 1' })
    store.setCurrentIteration(null)
    expect(store.currentIterationId).toBeNull()
    expect(localStorage.getItem('currentIterationId')).toBeNull()
  })

  it('clearCurrentIteration() removes from store and localStorage', () => {
    const store = useProjectStore()
    store.setCurrentIteration({ id: 'it-1', name: 'Sprint 1' })
    store.clearCurrentIteration()
    expect(store.currentIterationId).toBeNull()
    expect(localStorage.getItem('currentIterationId')).toBeNull()
  })

  it('initFromStorage() restores currentIterationId', () => {
    localStorage.setItem('currentProjectId', 'proj-1')
    localStorage.setItem('currentIterationId', 'it-42')
    const store = useProjectStore()
    store.initFromStorage()
    expect(store.currentIterationId).toBe('it-42')
  })
})
