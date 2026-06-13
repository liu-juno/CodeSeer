<template>
  <div class="modules-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">模块知识库</h1>
        <p class="page-subtitle">按模块组织需求与文档，自动沉淀领域知识</p>
      </div>
      <button class="btn btn-primary" @click="openCreate(null)">
        <span>＋</span> 新建模块
      </button>
    </div>

    <div class="modules-layout">
      <!-- Tree sidebar -->
      <div class="card module-tree-card">
        <div class="card-title">模块树</div>
        <div v-if="modules.length === 0" class="empty-state" style="padding:32px 0">
          <div class="empty-state-icon">⬡</div>
          <div class="empty-state-text">暂无模块</div>
        </div>
        <div v-else class="tree">
          <div
            v-for="m in flatTree"
            :key="m.id"
            :class="['tree-node', { active: selectedId === m.id }]"
            :style="{ paddingLeft: 14 + m.depth * 18 + 'px' }"
            @click="selectModule(m)"
          >
            <span class="tree-icon">{{ m.children?.length ? '▾' : '◦' }}</span>
            <span class="tree-name">{{ m.name }}</span>
            <span v-if="m.document_count" class="tree-badge">{{ m.document_count }}</span>
          </div>
        </div>
      </div>

      <!-- Module detail -->
      <div class="module-detail">
        <div v-if="!selected" class="card empty-card">
          <div class="empty-state">
            <div class="empty-state-icon">⬡</div>
            <div class="empty-state-text">从左侧选择一个模块</div>
          </div>
        </div>
        <template v-else>
          <div class="card module-header-card">
            <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:12px;">
              <div>
                <h2 class="module-title">{{ selected.name }}</h2>
                <p v-if="selected.description" class="text-muted text-medium" style="margin-top:6px">
                  {{ selected.description }}
                </p>
                <div class="text-small text-muted" style="margin-top:8px;">
                  路径：{{ selected.path || '/' }}{{ selected.name }} · {{ selected.document_count }} 份文档
                </div>
              </div>
              <div style="display:flex; gap:8px; flex-shrink:0;">
                <button class="btn btn-secondary" @click="openCreate(selected.id)">+ 子模块</button>
                <button class="btn btn-secondary" @click="editSelected">编辑</button>
                <button class="btn btn-primary" @click="generateSkill" :disabled="!selected.document_count || generating">
                  {{ generating ? '生成中...' : '⬡ 生成 Skill' }}
                </button>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-title">归档文档 ({{ moduleDocs.length }})</div>
            <div v-if="moduleDocs.length === 0" class="empty-state" style="padding:24px 0">
              <div class="empty-state-icon">▤</div>
              <div class="empty-state-text">该模块下暂无归档文档</div>
              <p class="text-muted text-small" style="margin-top:8px">
                归档 {{ moduleDocs.length === 0 ? '后' : '更多' }}文档可生成 Skill
              </p>
            </div>
            <table v-else class="table" style="margin:-4px -4px">
              <thead>
                <tr><th>标题</th><th>类型</th><th>版本</th><th>归档时间</th></tr>
              </thead>
              <tbody>
                <tr v-for="d in moduleDocs" :key="d.id">
                  <td style="font-weight:500">{{ d.title }}</td>
                  <td class="text-muted text-small">{{ d.document_type }}</td>
                  <td class="text-muted text-small">v{{ d.version }}</td>
                  <td class="text-muted text-small">{{ formatDate(d.archived_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="moduleSkill" class="card skill-card">
            <div class="card-title">已生成 Skill</div>
            <div class="skill-info">
              <div class="skill-name">{{ moduleSkill.name }} <span class="skill-version">v{{ moduleSkill.version }}</span></div>
              <div class="text-muted text-small" style="margin-top:4px">{{ moduleSkill.description }}</div>
              <pre class="skill-preview">{{ (moduleSkill.prompt_template || '').slice(0, 400) }}{{ (moduleSkill.prompt_template || '').length > 400 ? '...' : '' }}</pre>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal" style="width:480px;">
        <div class="modal-header">
          <h3>{{ editing ? '编辑模块' : '新建模块' }}</h3>
          <button class="modal-close" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">模块名称 <span class="required">*</span></label>
            <input v-model="form.name" class="form-input" placeholder="如：订单系统" autofocus />
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label class="form-label">描述</label>
            <textarea v-model="form.description" class="form-input" style="min-height:80px" placeholder="该模块负责什么..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeForm">取消</button>
          <button v-if="editing" class="btn btn-secondary danger" @click="deleteSelected">删除</button>
          <button class="btn btn-primary" :disabled="!form.name.trim() || saving" @click="saveModule">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { modulesApi, documentsApi } from '@/api'

const modules = ref<any[]>([])
const selectedId = ref<string | null>(null)
const selected = ref<any>(null)
const moduleDocs = ref<any[]>([])
const moduleSkill = ref<any>(null)
const showForm = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const generating = ref(false)
const form = ref({ name: '', description: '' })

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

const saveModule = async () => {
  saving.value = true
  try {
    const payload = { ...form.value, parent_id: editing.value?.parent_id || null }
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
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

const deleteSelected = async () => {
  if (!editing.value?.id) return
  if (!confirm(`删除模块「${editing.value.name}」？`)) return
  try {
    await modulesApi.delete(editing.value.id)
    closeForm()
    selectedId.value = null
    selected.value = null
    fetchData()
  } catch (e: any) { alert(e?.response?.data?.detail || '删除失败') }
}

const generateSkill = async () => {
  if (!selected.value) return
  if (!confirm(`基于该模块下 ${moduleDocs.value.length} 份归档文档生成 Skill？`)) return
  generating.value = true
  try {
    await modulesApi.generateSkill(selected.value.id)
    await selectModule(selected.value)
  } catch (e: any) { alert(e?.response?.data?.detail || '生成失败') }
  finally { generating.value = false }
}

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'

const fetchData = async () => {
  try {
    const res = await modulesApi.list()
    modules.value = res.data
  } catch (e) { console.error(e) }
}

onMounted(fetchData)
</script>

<style scoped>
.modules-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  align-items: flex-start;
}

.module-tree-card { padding: 12px 0; }
.tree { display: flex; flex-direction: column; }
.tree-node {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 14px; cursor: pointer;
  font-size: 13.5px; color: #374151;
  border-left: 3px solid transparent;
  transition: all 0.1s;
}
.tree-node:hover { background: #f9fafb; }
.tree-node.active {
  background: #eef2ff;
  border-left-color: #6366f1;
  color: #4338ca;
  font-weight: 600;
}
.tree-icon { font-size: 11px; color: #9ca3af; flex-shrink: 0; width: 12px; }
.tree-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tree-badge {
  background: #e0e7ff; color: #4338ca;
  font-size: 11px; font-weight: 600;
  padding: 1px 6px; border-radius: 10px;
}

.module-detail { display: flex; flex-direction: column; gap: 16px; }
.empty-card { min-height: 300px; display: flex; align-items: center; justify-content: center; }

.module-header-card { padding: 20px; }
.module-title { font-size: 18px; font-weight: 700; color: #111827; }

.skill-card {
  background: linear-gradient(135deg, #0f0f17 0%, #1a1a2e 100%);
  border-color: rgba(99,102,241,0.3);
  color: #e5e7eb;
}
.skill-card .card-title { color: #f9fafb; }
.skill-info { }
.skill-name { font-size: 15px; font-weight: 600; color: #f9fafb; }
.skill-version {
  font-size: 11px; color: #9ca3af;
  background: rgba(255,255,255,0.1);
  padding: 1px 6px; border-radius: 4px;
  margin-left: 8px; font-weight: 500;
}
.skill-preview {
  margin-top: 12px; padding: 14px;
  background: rgba(0,0,0,0.3);
  border-radius: 6px;
  font-family: monospace;
  font-size: 12px; line-height: 1.6;
  color: #a5b4fc; white-space: pre-wrap;
  max-height: 200px; overflow-y: auto;
}

.btn.danger { color: #dc2626; }
</style>
