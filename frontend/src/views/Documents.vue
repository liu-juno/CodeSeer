<template>
  <div class="documents-page">
    <div class="page-header">
    </div>

    <el-row :gutter="14" style="margin-bottom:16px;">
      <el-col :span="6"><el-card shadow="never" body-style="padding:16px;"><div style="display:flex; align-items:center; gap:14px;"><div class="stat-icon indigo">▤</div><div><div class="stat-value">{{ stats.total }}</div><div class="stat-label">总文档</div></div></div></el-card></el-col>
      <el-col :span="6"><el-card shadow="never" body-style="padding:16px;"><div style="display:flex; align-items:center; gap:14px;"><div class="stat-icon amber">✎</div><div><div class="stat-value">{{ stats.draft }}</div><div class="stat-label">草稿</div></div></div></el-card></el-col>
      <el-col :span="6"><el-card shadow="never" body-style="padding:16px;"><div style="display:flex; align-items:center; gap:14px;"><div class="stat-icon green">✓</div><div><div class="stat-value">{{ stats.archived }}</div><div class="stat-label">已归档</div></div></div></el-card></el-col>
      <el-col :span="6"><el-card shadow="never" body-style="padding:16px;"><div style="display:flex; align-items:center; gap:14px;"><div class="stat-icon purple">⬡</div><div><div class="stat-value">{{ modules.length }}</div><div class="stat-label">模块</div></div></div></el-card></el-col>
    </el-row>

    <div class="filters-bar mb-16">
      <el-input v-model="filter.search" placeholder="搜索文档标题或内容..." style="width:240px;" clearable />
      <el-select v-model="filter.status" placeholder="全部状态" style="width:130px;" clearable>
        <el-option value="draft" label="草稿" />
        <el-option value="archived" label="已归档" />
        <el-option value="deprecated" label="已废弃" />
      </el-select>
      <el-select v-model="filter.moduleId" placeholder="全部模块" style="width:200px;" clearable>
        <el-option v-for="m in flatModules" :key="m.id" :label="(projectNameById(m.project_id) ? '[' + projectNameById(m.project_id) + '] ' : '') + m.path + m.name" :value="m.id" />
      </el-select>
      <el-select v-model="filter.type" placeholder="全部类型" style="width:130px;" clearable>
        <el-option value="analysis" label="需求分析" />
        <el-option value="design" label="设计文档" />
        <el-option value="api" label="接口文档" />
        <el-option value="diagram" label="架构图" />
        <el-option value="other" label="其他" />
      </el-select>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon> 新建文档
      </el-button>
    </div>

    <el-card shadow="never" body-style="padding:0;">
      <el-table v-loading="loading" :data="displayedDocs" stripe>
        <el-table-column label="文档" min-width="250">
          <template #default="{ row }">
            <div style="display:flex; align-items:flex-start; gap:10px;">
              <span :class="['doc-type-icon', row.document_type]">{{ typeIcon(row.document_type) }}</span>
              <div>
                <div style="font-weight:600; font-size:13.5px; color:#111827;">{{ row.title }}</div>
                <el-text v-if="row.summary" type="info" size="small">{{ row.summary }}</el-text>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="document_type" label="类型" width="100">
          <template #default="{ row }">{{ typeText(row.document_type) }}</template>
        </el-table-column>
        <el-table-column label="模块" width="120">
          <template #default="{ row }">
            <el-text type="info" size="small">{{ getModuleName(row.module_id) || '未分类' }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="处理" width="100">
          <template #default="{ row }">
            <div style="display:flex; align-items:center; gap:4px;">
              <span :class="['processing-dot', row.processing_status]"></span>
              <el-text type="info" size="small">{{ processingText(row.processing_status) }}</el-text>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80">
          <template #default="{ row }">v{{ row.version }}</template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新于" width="120">
          <template #default="{ row }">
            <el-text type="info" size="small">{{ formatDate(row.updated_at) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="right">
          <template #default="{ row }">
            <el-button v-if="row.processing_status === 'pending'" text size="small" type="primary" @click="processDoc(row)">整理</el-button>
            <el-button v-if="row.status === 'draft'" text size="small" type="primary" @click="archiveDoc(row)">归档</el-button>
            <el-button text size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button text size="small" type="danger" @click="deleteDoc(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showForm" :title="editing ? '编辑文档' : '新建文档'" width="680px">
      <el-form :model="form" label-position="top">
        <el-form-item label="文档标题" required>
          <el-input v-model="form.title" placeholder="如：用户登录 API 设计" />
        </el-form-item>
        <el-row :gutter="14">
          <el-col :span="12">
            <el-form-item label="类型">
              <el-select v-model="form.document_type" style="width:100%;">
                <el-option value="analysis" label="需求分析" />
                <el-option value="design" label="设计文档" />
                <el-option value="api" label="接口文档" />
                <el-option value="diagram" label="架构图" />
                <el-option value="other" label="其他" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联模块">
              <el-select v-model="form.module_id" style="width:100%;" clearable>
                <el-option v-for="m in flatModules" :key="m.id" :label="(projectNameById(m.project_id) ? '[' + projectNameById(m.project_id) + '] ' : '') + m.path + m.name" :value="m.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item v-if="!editing" label="从本地上传（.md / .txt）">
          <el-upload
            :show-file-list="false"
            :before-upload="handleFileUpload"
            accept=".md,.txt"
            drag
            style="width:100%;"
          >
            <div style="padding:16px 0; color:#9ca3af; font-size:13px;">
              拖拽文件到此处，或 <el-text type="primary" style="cursor:pointer;">点击上传</el-text>
              <div style="font-size:12px; margin-top:4px;">支持 .md / .txt，内容将填入下方编辑框</div>
            </div>
          </el-upload>
        </el-form-item>
        <el-form-item label="文档内容（支持 Markdown）">
          <el-input v-model="form.content" type="textarea" :rows="10" placeholder="# 设计文档&#10;&#10;## 背景&#10;..." style="font-family:monospace; font-size:13px;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeForm">取消</el-button>
        <el-button type="primary" :loading="saving" :disabled="!form.title.trim()" @click="saveDoc">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { documentsApi, modulesApi, projectsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const docs = ref<any[]>([])
const modules = ref<any[]>([])
const projects = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editing = ref<any>(null)
const filter = ref({ search: '', status: '', moduleId: '', type: '' })
const form = ref({ title: '', document_type: 'design', module_id: '', content: '' })

const projectNameById = (id: string) => projects.value.find((p: any) => p.id === id)?.name || ''

const flatModules = computed(() => {
  const out: any[] = []
  const walk = (list: any[], prefix: string, projectId: string) => {
    for (const m of list) {
      const path = prefix + m.name + '/'
      out.push({ id: m.id, name: m.name, path: prefix, project_id: m.project_id ?? projectId })
      if (m.children?.length) walk(m.children, path, m.project_id ?? projectId)
    }
  }
  walk(modules.value, '', '')
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

const handleFileUpload = (file: File) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target?.result as string
    if (!form.value.title) {
      form.value.title = file.name.replace(/\.(md|txt)$/i, '')
    }
    form.value.content = text
  }
  reader.readAsText(file, 'utf-8')
  return false  // 阻止 el-upload 自动上传
}

const openCreate = () => {
  editing.value = null
  form.value = { title: '', document_type: 'design', module_id: '', content: '' }
  showForm.value = true
}

const openEdit = (doc: any) => {
  editing.value = doc
  form.value = { title: doc.title, document_type: doc.document_type, module_id: doc.module_id || '', content: doc.content || '' }
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
    ElMessage.success('保存成功')
    fetchData()
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

const archiveDoc = async (doc: any) => {
  try {
    await ElMessageBox.confirm(`归档文档「${doc.title}」？归档后不可编辑。`, '提示', { type: 'warning' })
    await documentsApi.archive(doc.id)
    ElMessage.success('归档成功')
    fetchData()
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

const processDoc = async (doc: any) => {
  try {
    await documentsApi.process(doc.id)
    ElMessage.success('整理完成')
    fetchData()
  } catch (e) { console.error(e) }
}

const deleteDoc = async (doc: any) => {
  try {
    await ElMessageBox.confirm(`删除文档「${doc.title}」？此操作不可恢复。`, '提示', { type: 'warning' })
    await documentsApi.delete(doc.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

const fetchData = async () => {
  loading.value = true
  try {
    const [dRes, mRes, pRes] = await Promise.all([documentsApi.list(), modulesApi.list(), projectsApi.list()])
    docs.value = dRes.data
    modules.value = mRes.data
    projects.value = pRes.data.items ?? pRes.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; }
.page-title { font-size:20px; font-weight:700; color:#1f2329; margin:0; }
.page-subtitle { font-size:13px; color:#969ba4; margin:4px 0 0 0; }
.filters-bar { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
.mb-16 { margin-bottom:16px; }
.stat-value { font-size:22px; font-weight:700; color:#1f2329; line-height:1; }
.stat-label { font-size:12px; color:#969ba4; margin-top:3px; }
.stat-icon { width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; }
.stat-icon.indigo { background:rgba(99,102,241,0.1); }
.stat-icon.amber { background:rgba(255,154,46,0.1); }
.stat-icon.green { background:rgba(0,168,112,0.1); }
.stat-icon.purple { background:rgba(139,92,246,0.1); }
.doc-type-icon { font-size:16px; line-height:1.2; margin-top:2px; width:24px; text-align:center; flex-shrink:0; }
.doc-type-icon.analysis { color:#6366f1; }
.doc-type-icon.design { color:#8b5cf6; }
.doc-type-icon.api { color:#10b981; }
.doc-type-icon.diagram { color:#f59e0b; }
.doc-type-icon.other { color:#6b7280; }
.processing-dot { display:inline-block; width:6px; height:6px; border-radius:50%; background:#d1d5db; margin-right:4px; }
.processing-dot.pending { background:#f59e0b; }
.processing-dot.processing { background:#6366f1; animation:pulse 1s infinite; }
.processing-dot.completed { background:#10b981; }
.processing-dot.failed { background:#ef4444; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
</style>
