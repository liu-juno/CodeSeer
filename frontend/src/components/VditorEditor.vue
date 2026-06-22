<template>
  <div ref="editorRef" class="vditor-editor"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import Vditor from 'vditor'
import 'vditor/dist/index.css'

const props = defineProps<{
  modelValue: string
  placeholder?: string
  height?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const editorRef = ref<HTMLElement>()
let vditor: Vditor | null = null

const handleValueChanged = (value: string) => {
  emit('update:modelValue', value)
}

onMounted(() => {
  const editorElement = editorRef.value!
  vditor = new Vditor(editorElement, {
    value: props.modelValue,
    placeholder: props.placeholder || '',
    height: parseInt(props.height || '300'),
    mode: 'wysiwyg',
    cache: { id: 'vditor-editor' },
    after: () => {
      editorElement.addEventListener('input', () => {
        if (vditor) {
          handleValueChanged(vditor.getValue())
        }
      })
    }
  })
})

onBeforeUnmount(() => {
  vditor?.destroy()
})

watch(() => props.modelValue, (newVal) => {
  if (vditor && vditor.getValue() !== newVal) {
    vditor.setValue(newVal)
  }
})
</script>

<style>
.vditor-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.vditor-editor .vditor {
  border: none;
  border-radius: 0;
}

.vditor-editor .vditor-toolbar {
  padding: 4px 8px;
  background: #f5f7fa;
  display: flex !important;
  flex-wrap: wrap;
  gap: 4px;
}

.vditor-editor .vditor-toolbar__icon {
  color: #586069;
}

.vditor-editor .vditor-toolbar__icon:hover {
  color: #4285f4;
  background: #e8e9eb;
}

.vditor-editor .vditor-toolbar__item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  color: #586069;
}

.vditor-editor .vditor-toolbar__item:hover {
  background: #e8e9eb;
  color: #4285f4;
}

.vditor-editor .vditor-icon {
  width: 16px;
  height: 16px;
  color: inherit;
}

.vditor-editor .vditor-icon svg {
  width: 100%;
  height: 100%;
  fill: currentColor;
}

.vditor-editor .vditor-content {
  background: #fff;
}
</style>