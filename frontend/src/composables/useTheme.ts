import { ref, watch } from 'vue'

const STORAGE_KEY = 'codeseer-theme'
const isDark = ref(false)
let _initialized = false

export function useTheme() {
  function init() {
    if (_initialized) return
    _initialized = true
    isDark.value = localStorage.getItem(STORAGE_KEY) === 'dark'
    document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
    watch(isDark, (val) => {
      document.documentElement.setAttribute('data-theme', val ? 'dark' : 'light')
      localStorage.setItem(STORAGE_KEY, val ? 'dark' : 'light')
    })
  }

  return { isDark, toggle: () => { isDark.value = !isDark.value }, init }
}
