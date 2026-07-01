<template>
  <div ref="editorRef" class="vditor-wrap"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import Vditor from 'vditor'
import 'vditor/dist/index.css'

const props = defineProps<{
  modelValue: string
  placeholder?: string
  height?: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const editorRef = ref<HTMLElement>()
let vditor: Vditor | null = null
let inited = false

// 每个实例用唯一 cache ID，避免多实例冲突
const cacheId = 'vditor-' + Math.random().toString(36).slice(2)

onMounted(() => {
  vditor = new Vditor(editorRef.value!, {
    value: props.modelValue || '',
    placeholder: props.placeholder || '支持 Markdown 语法...',
    height: props.height ?? 260,
    mode: 'ir',                    // instant rendering：单栏即时渲染
    cdn: '/vditor',                // 使用 public/vditor，不走外部 CDN
    cache: { enable: false },      // 关闭缓存，避免 localStorage 污染
    toolbar: [
      'headings', 'bold', 'italic', 'strike', '|',
      'list', 'ordered-list', 'check', '|',
      'code', 'inline-code', 'quote', '|',
      'link', 'table', '|',
      'undo', 'redo',
    ],
    input(value) {
      emit('update:modelValue', value)
    },
    after() {
      inited = true
    },
  })
})

onBeforeUnmount(() => {
  vditor?.destroy()
  vditor = null
})

watch(() => props.modelValue, (val) => {
  if (inited && vditor && vditor.getValue() !== val) {
    vditor.setValue(val ?? '')
  }
})
</script>

<style scoped>
.vditor-wrap {
  width: 100%;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-input);
  overflow: hidden;
}
:deep(.vditor) {
  width: 100% !important;
}
:deep(.vditor-ir) {
  width: 100% !important;
}
</style>
