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
  vditor = new Vditor(editorRef.value!, {
    value: props.modelValue,
    placeholder: props.placeholder || '',
    height: parseInt(props.height || '300'),
    mode: 'wysiwyg',
    cache: { id: 'vditor-editor' },
    after: () => {
      vditor!.getElement().addEventListener('input', () => {
        handleValueChanged(vditor!.getValue())
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

<style scoped>
.vditor-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}
</style>