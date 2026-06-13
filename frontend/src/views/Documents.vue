<template>
  <div class="documents-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">文档管理</h1>
        <p class="page-subtitle">按模块沉淀的设计文档、API 文档、知识积累</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <span>＋</span> 新建文档
      </button>
    </div>

    <!-- Stats -->
    <div class="stats-grid mb-16">
      <div class="stat-card">
        <div class="stat-icon indigo">▤</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总文档</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon amber">✎</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.draft }}</div>
          <div class="stat-label">草稿</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">✓</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.archived }}</div>
          <div class="stat-label">已归档</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon purple">⬡</div>
        <div class="stat-body">
          <div class="stat-value">{{ modules.length }}</div>
          <div class="stat-label">模块</div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-bar mb-16">
      <div class="search-wrap">
        <span class="search-icon">⌕</span>
        <input
          v-model="filter.search"
          class="form-input search-input"
          placeholder="搜索文档标题或内容..."
          style="padding-left:32px; width:240px;"
        />
      </div>
      <select v-model="filter.status" class="form-input" style="width:130px">
        <option value="">全部状态</option>
        <option value="draft">草稿</option>
        <option value="archived">已归档</option>
        <option value="deprecated">已废弃</option>
      </select>
      <select v-model="filter.moduleId" class="form-input" style="width:200px">
        <option value="">全部模块</option>
        <option v-for="m in flatModules" :key="m.id" :value="m.id">
          {{ m.path || '' }}{{ m.name }}
        </option>
      </select>
      <select v-model="filter.type" class="form-input" style="width:130px">
        <option value="">全部类型</option>
        <option value="analysis">需求分析</option>
        <option value="design">设计文档</option>
        <option value="api">接口文档</option>
        <option value="diagram">架构图</option>
        <option value="other">其他</option>
      </select>
    </div>

    <div class="card" style="padding:0; overflow:hidden;">
      <div v-if="loading" class="empty-state"><div class="empty-state-text text-muted">加载中...</div></div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>文档</th>
            <th>类型</th>
            <th>模块</th>
            <th>状态</th>
            <th>处理</th>
            <th>版本</th>
            <th>更新于</th>
            <th style="width:200px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in displayedDocs" :key="doc.id">
            <td>
              <div class="doc-title-cell">
                <span :class="['doc-type-icon', doc.document_type]">{{ typeIcon(doc.document_type) }}</span>
                <div>
                  <div class="doc-title">{{ doc.title }}</div>
                  <div v-if="doc.summary" class="doc-summary text-muted text-small">{{ doc.summary }}</div>
                </div>
              </div>
            </td>
            <td class="text-medium">{{ typeText(doc.document_type) }}</td>
            <td class="text-muted text-small">{{ getModuleName(doc.module_id) || '未分类' }}</td>
            <td>
              <span :class="['status-badge', doc.status]">{{ statusText(doc.status) }}</span>
            </td>
            <td>
              <span :class="['processing-dot', doc.processing_status]"></span>
              <span class="text-small text-muted">{{ processingText(doc.processing_status) }}</span>
            </td>
            <td class="text-muted text-small">v{{ doc.version }}</td>
            <td class="text-muted text-small">{{ formatDate(doc.updated_at) }}</td>
            <td>
              <div class="action-row">
                <button v-if="doc.processing_status === 'pending'" class="btn-link" @click="processDoc(doc)">整理</button>
                <button v-if="doc.status === 'draft'" class="btn-link" @click="archiveDoc(doc)">归档</button>
                <button class="btn-link" @click="openEdit(doc)">编辑</button>
                <button class="btn-link danger" @click="deleteDoc(doc)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="displayedDocs.length === 0">
            <td colspan="8">
              <div class="empty-state">
                <div class="empty-state-icon">▤</div>
                <div class="empty-state-text">暂无文档</div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Edit/Create Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal" style="width:680px; max-width:95vw;">
        <div class="modal-header">
          <h3>{{ editing ? '编辑文档' : '新建文档' }}</h3>
          <button class="modal-close" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">文档标题 <span class="required">*</span></label>
            <input v-model="form.title" class="form-input" placeholder="如：用户登录 API 设计" autofocus />
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px;">
            <div class="form-group" style="margin-bottom:0">
              <label class="form-label">类型</label>
              <select v-model="form.document_type" class="form-input">
                <option value="analysis">需求分析</option>
                <option value="design">设计文档</option>
                <option value="api">接口文档</option>
                <option value="diagram">架构图</option>
                <option value="other">其他</option>
              </select>
            </div>
            <div class="form-group" style="margin-bottom:0">
              <label class="form-label">关联模块</label>
              <select v-model="form.module_id" class="form-input">
                <option value="">未分类</option>
                <option v-for="m in flatModules" :key="m.id" :value="m.id">
                  {{ m.path || '' }}{{ m.name }}
                </option>
              </select>
            </div>
          </div>
          <div class="form-group" style="margin-top:14px; margin-bottom:0">
            <label class="form-label">文档内容（支持 Markdown）</label>
            <textarea
              v-model="form.content"
              class="form-input"
              style="min-height:260px; font-family: monospace; font-size: 13px;"
              placeholder="# 设计文档&#10;&#10;## 背景&#10;..."
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeForm">取消</button>
          <button class="btn btn-primary" :disabled="!form.title.trim() || saving" @click="saveDoc">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { documentsApi, modulesApi } from '@/api'

const docs = ref<any[]>([])
const modules = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editing = ref<any>(null)
const filter = ref({ search: '', status: '', moduleId: '', type: '' })

const form = ref({ title: '', document_type: 'design', module_id: '', content: '' })

const flatModules = computed(() => {
  const out: any[] = []
  const walk = (list: any[], prefix: string) => {
    for (const m of list) {
      const path = prefix + m.name + '/'
      out.push({ id: m.id, name: m.name, path: prefix })
      if (m.children?.length) walk(m.children, path)
    }
  }
  walk(modules.value, '')
  return out
})

const stats = computed(() => ({
  total: docs.value.length,
  draft: docs.value.filter(d => d.status === 'draft').length,
  archived: docs.value.filter(d => d.status === 'archived').length,
}))

const displayedDocs = computed(() => {
  let list = docs.value
  if (filter.value.search.trim()) {
    const q = filter.value.search.trim().toLowerCase()
    list = list.filter((d: any) =>
      d.title.toLowerCase().includes(q) ||
      (d.content || '').toLowerCase().includes(q) ||
      (d.summary || '').toLowerCase().includes(q)
    )
  }
  if (filter.value.status) list = list.filter((d: any) => d.status === filter.value.status)
  if (filter.value.moduleId) list = list.filter((d: any) => d.module_id === filter.value.moduleId)
  if (filter.value.type) list = list.filter((d: any) => d.document_type === filter.value.type)
  return list
})

const typeIcon = (t: string) => ({ analysis: '◇', design: '◆', api: '⌬', diagram: '⌖', other: '◦' }[t] || '◦')
const typeText = (t: string) => ({ analysis: '需求分析', design: '设计', api: 'API', diagram: '架构图', other: '其他' }[t] || t)
const statusText = (s: string) => ({ draft: '草稿', archived: '已归档', deprecated: '已废弃' }[s] || s)
const processingText = (p: string) => ({ pending: '待整理', processing: '整理中', completed: '已整理', failed: '失败' }[p] || p)
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'

const getModuleName = (id: string) => {
  if (!id) return ''
  const m = flatModules.value.find((m: any) => m.id === id)
  return m ? m.name : ''
}

const openCreate = () => {
  editing.value = null
  form.value = { title: '', document_type: 'design', module_id: '', content: '' }
  showForm.value = true
}

const openEdit = (doc: any) => {
  editing.value = doc
  form.value = {
    title: doc.title,
    document_type: doc.document_type,
    module_id: doc.module_id || '',
    content: doc.content || '',
  }
  showForm.value = true
}

const closeForm = () => { showForm.value = false }

const saveDoc = async () => {
  saving.value = true
  try {
    if (editing.value) {
      await documentsApi.update(editing.value.id, form.value)
    } else {
      await documentsApi.create(form.value)
    }
    closeForm()
    fetchData()
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

const archiveDoc = async (doc: any) => {
  if (!confirm(`归档文档「${doc.title}」？归档后不可编辑。`)) return
  try {
    await documentsApi.archive(doc.id)
    fetchData()
  } catch (e) { console.error(e) }
}

const processDoc = async (doc: any) => {
  try {
    await documentsApi.process(doc.id)
    fetchData()
  } catch (e) { console.error(e) }
}

const deleteDoc = async (doc: any) => {
  if (!confirm(`删除文档「${doc.title}」？此操作不可恢复。`)) return
  try {
    await documentsApi.delete(doc.id)
    fetchData()
  } catch (e) { console.error(e) }
}

const fetchData = async () => {
  loading.value = true
  try {
    const [dRes, mRes] = await Promise.all([documentsApi.list(), modulesApi.list()])
    docs.value = dRes.data
    modules.value = mRes.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.filters-bar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

.search-wrap { position: relative; display: flex; align-items: center; }
.search-icon {
  position: absolute; left: 10px; color: #9ca3af;
  font-size: 15px; pointer-events: none; z-index: 1;
}

.doc-title-cell { display: flex; align-items: flex-start; gap: 10px; }
.doc-type-icon {
  font-size: 16px; line-height: 1.2; margin-top: 2px;
  width: 24px; text-align: center; flex-shrink: 0;
}
.doc-type-icon.analysis { color: #6366f1; }
.doc-type-icon.design   { color: #8b5cf6; }
.doc-type-icon.api      { color: #10b981; }
.doc-type-icon.diagram  { color: #f59e0b; }
.doc-type-icon.other    { color: #6b7280; }

.doc-title { font-size: 13.5px; font-weight: 600; color: #111827; }
.doc-summary {
  margin-top: 2px; max-width: 380px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.processing-dot {
  display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  margin-right: 4px; background: #d1d5db;
}
.processing-dot.pending    { background: #f59e0b; }
.processing-dot.processing { background: #6366f1; animation: pulse 1s infinite; }
.processing-dot.completed  { background: #10b981; }
.processing-dot.failed     { background: #ef4444; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

.action-row { display: flex; gap: 12px; }
.btn-link {
  background: none; border: none; cursor: pointer;
  color: #6366f1; font-size: 13px; padding: 0;
}
.btn-link:hover { text-decoration: underline; }
.btn-link.danger { color: #dc2626; }
</style>
