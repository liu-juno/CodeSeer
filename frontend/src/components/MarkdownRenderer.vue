<template>
  <el-tabs v-model="activeTab" class="markdown-renderer">
    <el-tab-pane label="预览" name="preview">
      <div
        class="markdown-body"
        v-html="renderedHtml"
        :style="{ maxHeight: height || '300px', overflow: 'auto' }"
      ></div>
    </el-tab-pane>
    <el-tab-pane label="源码" name="source">
      <pre
        class="source-code"
        :style="{ maxHeight: height || '300px', overflow: 'auto' }"
      >{{ content }}</pre>
    </el-tab-pane>
  </el-tabs>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{
  content: string
  height?: string
}>()

const activeTab = ref('preview')

const renderedHtml = computed(() => {
  if (!props.content) return ''
  return marked(props.content)
})
</script>

<style scoped>
.markdown-body {
  padding: 16px;
  line-height: 1.6;
}

.markdown-body :deep(h1) { font-size: 1.5em; margin: 0.5em 0; }
.markdown-body :deep(h2) { font-size: 1.3em; margin: 0.5em 0; }
.markdown-body :deep(h3) { font-size: 1.1em; margin: 0.5em 0; }
.markdown-body :deep(p) { margin: 0.5em 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 1.5em; margin: 0.5em 0; }
.markdown-body :deep(code) { background: #f5f5f5; padding: 0.2em 0.4em; border-radius: 3px; }
.markdown-body :deep(pre) { background: #f5f5f5; padding: 1em; overflow: auto; border-radius: 4px; }

.source-code {
  margin: 0;
  padding: 16px;
  background: #f5f5f5;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>