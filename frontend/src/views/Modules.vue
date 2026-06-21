<template>
  <div class="modules-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">模块知识库</h1>
        <p class="page-subtitle">按模块组织需求与文档，自动沉淀领域知识</p>
      </div>
      <div style="display:flex; align-items:center; gap:10px;">
        <el-select
          v-model="selectedProjectId"
          placeholder="选择项目"
          style="width:200px;"
          @change="onProjectChange"
        >
          <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button type="primary" :disabled="!selectedProjectId" @click="openCreate(null)">
          <el-icon><Plus /></el-icon> 新建模块
        </el-button>
      </div>
    </div>

    <div class="modules-layout">
      <el-card shadow="never" body-style="padding:12px 0;" style="width:280px;">
        <template #header>
          <div style="font-weight:600;">模块树</div>
        </template>
        <el-empty v-if="modules.length === 0" description="暂无模块" />
        <div v-else>
          <div
            v-for="m in flatTree"
            :key="m.id"
            :class="['tree-node', { active: selectedId === m.id }]"
            :style="{ paddingLeft: 14 + m.depth * 18 + 'px' }"
            @click="selectModule(m)"
          >
            <span class="tree-icon">{{ m.children?.length ? '▾' : '◦' }}</span>
            <span class="tree-name">{{ m.name }}</span>
            <el-badge v-if="m.document_count" :value="m.document_count" size="small" />
          </div>
        </div>
      </el-card>

      <div class="module-detail">
        <el-card shadow="never" v-if="!selected">
          <el-empty description="从左侧选择一个模块" />
        </el-card>
        <template v-else>
          <el-card shadow="never" style="margin-bottom:16px;">
            <template #header>
              <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:12px;">
                <div>
                  <h2 class="module-title">{{ selected.name }}</h2>
                  <el-text v-if="selected.description" type="info" style="margin-top:6px; display:block;">{{ selected.description }}</el-text>
                  <el-text type="info" size="small" style="margin-top:8px; display:block;">
                    路径：{{ selected.path || '/' }}{{ selected.name }} · {{ selected.document_count }} 份文档
                  </el-text>
                </div>
                <div style="display:flex; gap:8px; flex-shrink:0;">
                  <el-button @click="openCreate(selected.id)">+ 子模块</el-button>
                  <el-button @click="editSelected">编辑</el-button>
                  <el-button v-if="isAdmin" type="danger" plain @click="deleteSelected">删除</el-button>
                  <el-button type="primary" :disabled="!selected.document_count" @click="openSkillDialog">⬡ 创建 Skill</el-button>
                </div>
              </div>
            </template>
          </el-card>

          <!-- 归档文档卡片区 -->
          <div class="section-title">归档文档 <span class="section-count">{{ moduleDocs.length }}</span></div>
          <el-empty v-if="moduleDocs.length === 0" description="该模块下暂无归档文档" style="padding:24px 0;" />
          <div v-else class="doc-cards">
            <div v-for="doc in moduleDocs" :key="doc.id" class="doc-card">
              <div class="doc-card-icon" :class="doc.document_type">{{ docTypeIcon(doc.document_type) }}</div>
              <div class="doc-card-body">
                <div class="doc-card-title">{{ doc.title }}</div>
                <div class="doc-card-meta">
                  <el-tag size="small" effect="plain">{{ docTypeText(doc.document_type) }}</el-tag>
                  <span class="doc-card-version">v{{ doc.version }}</span>
                  <span class="doc-card-date">{{ formatDate(doc.archived_at) }}</span>
                </div>
                <div v-if="doc.summary" class="doc-card-summary">{{ doc.summary }}</div>
              </div>
            </div>
          </div>

          <!-- Skill 卡片 -->
          <div class="section-title" style="margin-top:24px;">Skill</div>
          <div v-if="!moduleSkill" class="skill-empty">
            <span style="color:#9ca3af; font-size:13px;">尚未创建 Skill，点击右上角「创建 Skill」生成</span>
          </div>
          <div v-else class="skill-card">
            <div class="skill-card-header">
              <div>
                <span class="skill-card-name">{{ moduleSkill.name }}</span>
                <span class="skill-card-version">v{{ moduleSkill.version }}</span>
              </div>
              <div style="display:flex; align-items:center; gap:8px;">
                <el-tag size="small" type="success" effect="dark">active</el-tag>
                <el-button v-if="isAdmin" size="small" type="danger" text @click="deleteSkill" style="color:#f87171; padding:0;">删除</el-button>
              </div>
            </div>
            <div v-if="moduleSkill.description" class="skill-card-desc">{{ moduleSkill.description }}</div>
            <pre class="skill-card-prompt">{{ moduleSkill.prompt_template }}</pre>
          </div>
        </template>
      </div>
    </div>

    <el-dialog v-model="showSkillDialog" title="创建 Skill" width="560px" @closed="resetSkillForm">
      <el-form label-position="top">
        <el-form-item label="功能名称" required>
          <el-input v-model="skillForm.name" placeholder="如：领域知识" />
          <div style="margin-top:6px; font-size:12px; color:#9ca3af;">
            完整 Skill 名：<strong style="color:#d1d5db;">{{ skillFullName }}</strong>
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="skillForm.description" placeholder="简要说明此 Skill 的用途..." />
        </el-form-item>
        <el-form-item label="选择文档（至少勾选一份归档文档）">
          <div v-if="moduleDocs.length === 0" style="color:#9ca3af; font-size:13px;">该模块下暂无归档文档</div>
          <div v-else style="border:1px solid var(--el-border-color); border-radius:6px; max-height:240px; overflow-y:auto;">
            <div
              v-for="doc in moduleDocs"
              :key="doc.id"
              style="display:flex; align-items:center; gap:10px; padding:10px 14px; border-bottom:1px solid var(--el-border-color-lighter);"
            >
              <el-checkbox :value="doc.id" v-model="skillForm.document_ids" />
              <div>
                <div style="font-size:13.5px; font-weight:500;">{{ doc.title }}</div>
                <el-text type="info" size="small">{{ doc.document_type }} · v{{ doc.version }}</el-text>
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSkillDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="generating"
          :disabled="!skillForm.name.trim() || skillForm.document_ids.length === 0"
          @click="generateSkill"
        >创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showForm" :title="editing?.id ? '编辑模块' : '新建模块'" width="480px">
      <el-form :model="form" label-position="top">
        <el-form-item label="模块名称" required>
          <el-input v-model="form.name" placeholder="如：订单系统" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="该模块负责什么..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeForm">取消</el-button>
        <el-button v-if="editing?.id" type="danger" @click="deleteSelected">删除</el-button>
        <el-button type="primary" :loading="saving" :disabled="!form.name.trim()" @click="saveModule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { modulesApi, projectsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const projects = ref<any[]>([])
const selectedProjectId = ref<string | null>(null)
const modules = ref<any[]>([])
const selectedId = ref<string | null>(null)
const selected = ref<any>(null)
const moduleDocs = ref<any[]>([])
const moduleSkill = ref<any>(null)
const showForm = ref(false)
const showSkillDialog = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const generating = ref(false)
const form = ref({ name: '', description: '' })
const skillForm = ref({ name: '', description: '', document_ids: [] as string[] })

const selectedProject = computed(() => projects.value.find(p => p.id === selectedProjectId.value))

const skillFullName = computed(() => {
  const parts = [
    selectedProject.value?.name,
    selected.value?.name,
    skillForm.value.name.trim(),
  ].filter(Boolean)
  return parts.join('_') || '—'
})

const flatTree = computed(() => {
  const out: any[] = []
  const walk = (list: any[], depth: number) => {
    for (const m of list) {
      out.push({ ...m, depth })
      if (m.children?.length) walk(m.children, depth + 1)
    }
  }
  walk(modules.value, 0)
  return out
})

const selectModule = async (m: any) => {
  selectedId.value = m.id
  selected.value = m
  const [dRes, kRes] = await Promise.all([
    modulesApi.documents(m.id),
    modulesApi.knowledge(m.id),
  ])
  moduleDocs.value = dRes.data.filter((d: any) => d.status === 'archived')
  moduleSkill.value = kRes.data.skills?.[0] || null
}

const openCreate = (parentId: string | null) => {
  editing.value = parentId ? { parent_id: parentId } : null
  form.value = { name: '', description: '' }
  showForm.value = true
}

const editSelected = () => {
  if (!selected.value) return
  editing.value = selected.value
  form.value = { name: selected.value.name, description: selected.value.description || '' }
  showForm.value = true
}

const closeForm = () => { showForm.value = false }

const onProjectChange = () => {
  selectedId.value = null
  selected.value = null
  moduleDocs.value = []
  moduleSkill.value = null
  fetchData()
}

const saveModule = async () => {
  saving.value = true
  try {
    const payload = { ...form.value, parent_id: editing.value?.parent_id || null, project_id: selectedProjectId.value }
    if (editing.value?.id) {
      await modulesApi.update(editing.value.id, payload)
    } else {
      const res = await modulesApi.create(payload)
      selectedId.value = res.data.id
    }
    closeForm()
    await fetchData()
    if (selectedId.value) {
      const m = flatTree.value.find((m: any) => m.id === selectedId.value)
      if (m) selectModule(m)
    }
    ElMessage.success('保存成功')
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

const deleteSelected = async () => {
  const target = editing.value?.id ? editing.value : selected.value
  if (!target?.id) return
  try {
    await ElMessageBox.confirm(`删除模块「${target.name}」？此操作不可撤销。`, '确认删除', { type: 'warning', confirmButtonText: '删除', confirmButtonClass: 'el-button--danger' })
    await modulesApi.delete(target.id)
    closeForm()
    selectedId.value = null
    selected.value = null
    await fetchData()
    ElMessage.success('删除成功')
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

const openSkillDialog = () => {
  skillForm.value = {
    name: '领域知识',
    description: '',
    document_ids: [],
  }
  showSkillDialog.value = true
}

const resetSkillForm = () => {
  skillForm.value = { name: '', description: '', document_ids: [] }
}

const generateSkill = async () => {
  if (!selected.value) return
  generating.value = true
  try {
    await modulesApi.generateSkill(selected.value.id, {
      name: skillForm.value.name,
      description: skillForm.value.description,
      document_ids: skillForm.value.document_ids,
    })
    showSkillDialog.value = false
    await selectModule(selected.value)
    ElMessage.success('Skill 创建成功')
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '创建失败') }
  finally { generating.value = false }
}

const deleteSkill = async () => {
  if (!selected.value) return
  try {
    await ElMessageBox.confirm(`删除 Skill「${moduleSkill.value?.name}」？`, '确认删除', { type: 'warning', confirmButtonText: '删除', confirmButtonClass: 'el-button--danger' })
    await modulesApi.deleteSkill(selected.value.id)
    moduleSkill.value = null
    ElMessage.success('Skill 已删除')
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'
const docTypeIcon = (t: string) => ({ analysis: '◇', design: '◆', api: '⌬', diagram: '⌖', other: '◦' }[t] || '◦')
const docTypeText = (t: string) => ({ analysis: '需求分析', design: '设计文档', api: 'API 文档', diagram: '架构图', other: '其他' }[t] || t)

const fetchData = async () => {
  try {
    const params = selectedProjectId.value ? { project_id: selectedProjectId.value } : {}
    const res = await modulesApi.list(params)
    modules.value = res.data
  } catch (e) { console.error(e) }
}

const fetchProjects = async () => {
  try {
    const res = await projectsApi.list()
    const items = res.data.items ?? res.data
    projects.value = items
    if (items.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = items[0].id
      fetchData()
    }
  } catch (e) { console.error(e) }
}

onMounted(fetchProjects)
</script>

<style scoped>
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; }
.page-title { font-size:20px; font-weight:700; color:#1f2329; margin:0; }
.page-subtitle { font-size:13px; color:#969ba4; margin:4px 0 0 0; }
.modules-layout { display:flex; gap:16px; align-items:flex-start; }
.module-detail { flex:1; display:flex; flex-direction:column; gap:0; }
.tree-node {
  display:flex; align-items:center; gap:6px;
  padding:7px 14px; cursor:pointer;
  font-size:13.5px; color:#374151;
  border-left:3px solid transparent;
  transition:all 0.1s;
}
.tree-node:hover { background:#f9fafb; }
.tree-node.active {
  background:#eef2ff;
  border-left-color:#6366f1;
  color:#4338ca;
  font-weight:600;
}
.tree-icon { font-size:11px; color:#9ca3af; flex-shrink:0; width:12px; }
.tree-name { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.module-title { font-size:18px; font-weight:700; color:#111827; margin:0; }

/* 区块标题 */
.section-title {
  font-size:13px; font-weight:600; color:#6b7280;
  text-transform:uppercase; letter-spacing:.05em;
  margin:20px 0 12px;
}
.section-count {
  display:inline-flex; align-items:center; justify-content:center;
  min-width:20px; height:20px; padding:0 6px;
  background:#f3f4f6; border-radius:10px;
  font-size:12px; color:#6b7280; margin-left:6px;
}

/* 文档卡片 */
.doc-cards { display:flex; flex-direction:column; gap:10px; }
.doc-card {
  display:flex; align-items:flex-start; gap:14px;
  padding:14px 16px;
  background:#fff; border:1px solid #e5e7eb; border-radius:10px;
  transition:box-shadow .15s;
}
.doc-card:hover { box-shadow:0 2px 8px rgba(0,0,0,.07); }
.doc-card-icon {
  width:36px; height:36px; border-radius:8px; flex-shrink:0;
  display:flex; align-items:center; justify-content:center;
  font-size:16px; background:#f3f4f6;
}
.doc-card-icon.design { background:#ede9fe; color:#7c3aed; }
.doc-card-icon.analysis { background:#e0e7ff; color:#4338ca; }
.doc-card-icon.api { background:#d1fae5; color:#065f46; }
.doc-card-icon.diagram { background:#fef3c7; color:#92400e; }
.doc-card-icon.other { background:#f3f4f6; color:#6b7280; }
.doc-card-body { flex:1; min-width:0; }
.doc-card-title { font-size:14px; font-weight:600; color:#111827; margin-bottom:6px; }
.doc-card-meta { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.doc-card-version { font-size:12px; color:#9ca3af; }
.doc-card-date { font-size:12px; color:#9ca3af; margin-left:auto; }
.doc-card-summary {
  font-size:12.5px; color:#6b7280; line-height:1.5;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
}

/* Skill 卡片 */
.skill-empty {
  padding:20px; border:1px dashed #e5e7eb; border-radius:10px;
  text-align:center;
}
.skill-card {
  border-radius:12px; overflow:hidden;
  background:linear-gradient(135deg, #0f0f17 0%, #1a1a2e 100%);
  border:1px solid rgba(99,102,241,.3);
  padding:20px;
}
.skill-card-header {
  display:flex; align-items:center; justify-content:space-between;
  margin-bottom:8px;
}
.skill-card-name { font-size:15px; font-weight:700; color:#f9fafb; }
.skill-card-version {
  font-size:11px; color:#9ca3af;
  background:rgba(255,255,255,.1); padding:1px 7px; border-radius:4px;
  margin-left:8px;
}
.skill-card-desc { font-size:13px; color:#9ca3af; margin-bottom:14px; }
.skill-card-prompt {
  padding:14px; margin:0;
  background:rgba(0,0,0,.35); border-radius:8px;
  font-family:monospace; font-size:12px; line-height:1.7;
  color:#a5b4fc; white-space:pre-wrap;
  max-height:220px; overflow-y:auto;
}
</style>
