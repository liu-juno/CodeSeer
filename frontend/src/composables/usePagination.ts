import { ref } from 'vue'

export function usePagination<T>(
  fetcher: (page: number, pageSize: number) => Promise<{ items: T[]; total: number }>
) {
  const items = ref<T[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)

  const fetchPage = async (p: number) => {
    loading.value = true
    try {
      const res = await fetcher(p, pageSize.value)
      items.value = res.items
      total.value = res.total
      page.value = p
    } finally {
      loading.value = false
    }
  }

  const onPageChange = (p: number) => fetchPage(p)
  const onSizeChange = (size: number) => {
    pageSize.value = size
    fetchPage(1)
  }

  return { items, total, page, pageSize, loading, fetchPage, onPageChange, onSizeChange }
}
