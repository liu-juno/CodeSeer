<template>
  <div class="modules-page">
    <div class="page-header">
      <el-button type="primary" @click="openCreate(null)">
        <el-icon><Plus /></el-icon> 新建模块
      </el-button>
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
                  <div class="module-stats">
                    <span>路径：{{ selected.path || '/' }}{{ selected.name }}</span>
                    <el-divider direction="vertical" />
                    <span>{{ moduleDocs.length }} 份文档</span>
                    <el-divider direction="vertical" />
                    <span>{{ selected.children?.length || 0 }} 个子模块</span>
                  </div>
                </div>
                <div style="display:flex; gap:8px; flex-shrink:0;">
                  <el-button @click="openCreate(selected.id)">+ 子模块</el-button>
                  <el-button @click="editSelected">编辑</el-button>
                  <el-button v-if="isAdmin" type="danger" plain @click="deleteSelected">删除</el-button>
                </div>
              </div>
            </template>
          </el-card>

          <el-tabs v-model="activeTab" class="module-tabs">
            <el-tab-pane name="docs">
              <template #label>
                <span>文档</span>
                <el-badge v-if="moduleDocs.length" :value="moduleDocs.length" style="margin-left:6px;" />
              </template>

              <div style="display:flex; justify-content:flex-end; gap:8px; margin-bottom:16px;">
                <el-button size="small" @click="openMergeDialog">合并生成</el-button>
                <el-button size="small" @click="openAddDocDialog">关联已有文档</el-button>
              </div>

              <el-empty v-if="moduleDocs.length === 0" description="该模块下暂无文档" />

              <template v-for="typeKey in docTypeOrder" :key="typeKey">
                <template v-if="docsByType[typeKey]?.length">
                  <div class="type-section-header">
                    <span class="type-section-label">{{ docTypeText(typeKey) }}</span>
                    <span class="section-count">{{ docsByType[typeKey].length }}</span>
                  </div>
                  <div class="doc-cards" style="margin-bottom:20px;">
                    <div v-for="doc in docsByType[typeKey]" :key="doc.id" class="doc-card">
                      <div class="doc-card-icon" :class="doc.document_type">{{ docTypeIcon(doc.document_type) }}</div>
                      <div class="doc-card-body">
                        <div class="doc-card-title">{{ doc.title }}</div>
                        <div class="doc-card-meta">
                          <el-tag size="small" :type="doc.status === 'archived' ? 'success' : 'info'" effect="plain">
                            {{ doc.status === 'archived' ? '已发布' : '草稿' }}
                          </el-tag>
                          <span class="doc-card-version">v{{ doc.version }}</span>
                          <span class="doc-card-date">{{ formatDate(doc.updated_at) }}</span>
                        </div>
                        <div v-if="doc.summary" class="doc-card-summary">{{ doc.summary }}</div>
                        <div v-if="doc.source_document_ids?.length" style="margin-top:4px;">
                          <el-tag size="small" type="warning" effect="plain">合并文档 · 源自 {{ doc.source_document_ids.length }} 份</el-tag>
                        </div>
                      </div>
                      <div class="doc-card-actions">
                        <el-button text size="small" @click="openViewDoc(doc)">查看</el-button>
                        <el-button text size="small" type="primary" @click="openEditDoc(doc)">编辑</el-button>
                        <el-button v-if="doc.status === 'draft'" text size="small" type="success" @click="publishDoc(doc)">发布</el-button>
                        <el-button text size="small" type="danger" @click="removeDoc(doc)">移除</el-button>
                      </div>
                    </div>
                  </div>
                </template>
              </template>
            </el-tab-pane>

            <el-tab-pane label="Skill" name="skill">
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
                    <el-button size="small" text @click="openEditSkill" style="color:#a5b4fc; padding:0;">编辑</el-button>
                    <el-button v-if="isAdmin" size="small" type="danger" text @click="deleteSkill" style="color:#f87171; padding:0;">删除</el-button>
                  </div>
                </div>
                <div v-if="moduleSkill.description" class="skill-card-desc">{{ moduleSkill.description }}</div>
                <pre class="skill-card-prompt">{{ moduleSkill.prompt_template }}</pre>
              </div>
            </el-tab-pane>
          </el-tabs>
        </template>
      </div>
    </div>

    <!-- 查看文档 dialog -->
    <el-dialog v-model="showViewDoc" :title="viewingDoc?.title" width="85%" destroy-on-close>
      <div v-if="viewingDoc" style="display:flex; gap:16px; min-height:500px;">
        <div style="flex:1; min-width:0; border:1px solid var(--el-border-color); border-radius:8px; overflow:hidden;">
          <div style="padding:10px 16px; border-bottom:1px solid var(--el-border-color); display:flex; align-items:center; gap:8px; background:#fafafa;">
            <el-tag size="small" effect="plain">{{ docTypeText(viewingDoc.document_type) }}</el-tag>
            <el-tag size="small" :type="viewingDoc.status === 'archived' ? 'success' : 'info'" effect="plain">
              {{ viewingDoc.status === 'archived' ? '已发布' : '草稿' }}
            </el-tag>
            <span style="font-size:12px; color:#9ca3af; margin-left:auto;">
              {{ viewingVersion ? `v${viewingVersion.version} · ${formatDate(viewingVersion.created_at)}` : `v${viewingDoc.version} · 当前版本` }}
            </span>
          </div>
          <div style="max-height:520px; overflow-y:auto;">
            <MarkdownRenderer :content="viewCurrentContent" height="520px" />
          </div>
        </div>
        <div style="width:260px; flex-shrink:0; border:1px solid var(--el-border-color); border-radius:8px; overflow:hidden;">
          <div style="padding:10px 16px; border-bottom:1px solid var(--el-border-color); background:#fafafa; font-size:13px; font-weight:600; color:#374151;">
            版本历史
          </div>
          <div style="max-height:560px; overflow-y:auto;">
            <el-skeleton :loading="loadingVersions" :rows="4" animated style="padding:12px;">
              <template #default>
                <div v-if="viewDocVersions.length === 0" style="padding:20px; text-align:center; color:#9ca3af; font-size:13px;">暂无版本记录</div>
                <div
                  v-for="ver in viewDocVersions"
                  :key="ver.id"
                  :class="['version-item', { active: viewingVersion?.id === ver.id }]"
                  @click="selectVersion(ver)"
                >
                  <div style="display:flex; align-items:center; justify-content:space-between;">
                    <span class="version-num">v{{ ver.version }}</span>
                    <span class="version-date">{{ formatDate(ver.created_at) }}</span>
                  </div>
                  <div v-if="ver.change_note" class="version-note">{{ ver.change_note }}</div>
                </div>
              </template>
            </el-skeleton>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button v-if="viewingVersion" @click="viewingVersion = null">回到最新版本</el-button>
        <el-button @click="showViewDoc = false">关闭</el-button>
        <el-button type="primary" @click="openEditFromView">编辑</el-button>
      </template>
    </el-dialog>

    <!-- 编辑文档 dialog -->
    <el-dialog v-model="showEditDoc" title="编辑文档" width="720px" destroy-on-close>
      <el-form :model="editDocForm" label-position="top">
        <div style="display:flex; gap:12px;">
          <el-form-item label="文档标题" required style="flex:1;">
            <el-input v-model="editDocForm.title" placeholder="输入文档标题..." />
          </el-form-item>
          <el-form-item label="文档类型" style="width:160px;">
            <el-select v-model="editDocForm.document_type">
              <el-option value="analysis" label="需求文档" />
              <el-option value="design" label="设计文档" />
              <el-option value="api" label="API 文档" />
              <el-option value="diagram" label="架构图" />
              <el-option value="other" label="其他" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="内容（支持 Markdown）">
          <VditorEditor v-model="editDocForm.content" :height="320" placeholder="输入文档内容，支持 Markdown..." />
        </el-form-item>
        <el-form-item label="更新说明（可选）">
          <el-input v-model="editDocForm.change_note" placeholder="简要描述此次修改内容..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDoc = false">取消</el-button>
        <el-button type="primary" :loading="savingEditDoc" :disabled="!editDocForm.title.trim()" @click="saveEditDoc">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑 Skill dialog -->
    <el-dialog v-model="showEditSkillDialog" title="编辑 Skill" width="440px">
      <el-form label-position="top">
        <el-form-item label="Skill 名称" required>
          <el-input v-model="skillEditForm.name" placeholder="如：cs_mcp" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="skillEditForm.description" type="textarea" :rows="2" placeholder="简要描述用途..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditSkillDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingSkill" :disabled="!skillEditForm.name.trim()" @click="saveSkillMeta">保存</el-button>
      </template>
    </el-dialog>

    <!-- 合并生成文档 dialog -->
    <el-dialog v-model="showMergeDialog" title="合并生成文档" width="580px">
      <el-form label-position="top">
        <el-form-item label="合并后文档标题" required>
          <el-input v-model="mergeForm.title" placeholder="如：XXX 模块完整设计文档" />
        </el-form-item>
        <el-form-item label="选择要合并的文档（可多选）">
          <el-input v-model="mergeDocSearch" placeholder="搜索文档标题..." clearable style="margin-bottom:10px;" />
          <div style="border:1px solid var(--el-border-color); border-radius:6px; max-height:300px; overflow-y:auto;">
            <el-empty v-if="filterMergeDocs.length === 0" description="没有可合并的文档" style="padding:20px;" />
            <div
              v-for="doc in filterMergeDocs"
              :key="doc.id"
              :class="['merge-doc-item', { selected: mergeDocSelected.includes(doc.id) }]"
              @click="toggleMergeDoc(doc.id)"
            >
              <el-checkbox :model-value="mergeDocSelected.includes(doc.id)" />
              <div style="min-width:0; flex:1;">
                <div style="font-size:13px; font-weight:500;">{{ doc.title }}</div>
                <el-text type="info" size="small">{{ docTypeText(doc.document_type) }} · v{{ doc.version }}</el-text>
              </div>
            </div>
          </div>
          <div style="font-size:12px; color:#6b7280; margin-top:8px;">
            已选 <strong>{{ mergeDocSelected.length }}</strong> 份
            <span v-if="mergeDocSelected.length >= 2" style="color:#10b981; margin-left:8px;">✓ 可合并</span>
            <span v-else style="color:#f59e0b; margin-left:8px;">请至少选择 2 份</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMergeDialog = false">取消</el-button>
        <el-button type="primary" :loading="merging" :disabled="mergeDocSelected.length < 2 || !mergeForm.title.trim()" @click="doMerge">
          AI 合并生成
        </el-button>
      </template>
    </el-dialog>

    <!-- 关联已有文档 dialog -->
    <el-dialog v-model="showAddDocDialog" title="关联已有归档文档到模块" width="560px">
      <el-input v-model="addDocSearch" placeholder="搜索文档标题..." clearable style="margin-bottom:12px;" />
      <div style="border:1px solid var(--el-border-color); border-radius:6px; max-height:360px; overflow-y:auto;">
        <el-empty v-if="filteredAvailableDocs.length === 0" description="没有可关联的归档文档" style="padding:24px;" />
        <div
          v-for="doc in filteredAvailableDocs"
          :key="doc.id"
          style="display:flex; align-items:center; gap:10px; padding:10px 14px; border-bottom:1px solid var(--el-border-color-lighter);"
        >
          <el-checkbox :value="doc.id" v-model="addDocSelected" />
          <div style="min-width:0; flex:1;">
            <div style="font-size:13px; font-weight:500;">{{ doc.title }}</div>
            <el-text type="info" size="small">{{ docTypeText(doc.document_type) }}</el-text>
          </div>
        </div>
      </div>
      <div style="font-size:12px; color:#6b7280; margin-top:8px;">已选 <strong>{{ addDocSelected.length }}</strong> 份</div>
      <template #footer>
        <el-button @click="showAddDocDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingDocs" :disabled="addDocSelected.length === 0" @click="confirmAddDocs">确认关联</el-button>
      </template>
    </el-dialog>

    <!-- 模块表单 dialog -->
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
import { modulesApi, documentsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

const authStore = useAuthStore()
const projectStore = useProjectStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const modules = ref<any[]>([])
const selectedId = ref<string | null>(null)
const selected = ref<any>(null)
const moduleDocs = ref<any[]>([])
const moduleSkill = ref<any>(null)
const showForm = ref(false)
const activeTab = ref('docs')
const editing = ref<any>(null)
const saving = ref(false)
const form = ref({ name: '', description: '' })

// ── Skill 编辑 ────────────────────────────────────────────────────────────────
const showEditSkillDialog = ref(false)
const skillEditForm = ref({ name: '', description: '' })
const savingSkill = ref(false)

const openEditSkill = () => {
  skillEditForm.value = { name: moduleSkill.value?.name || '', description: moduleSkill.value?.description || '' }
  showEditSkillDialog.value = true
}

const saveSkillMeta = async () => {
  if (!selected.value) return
  savingSkill.value = true
  try {
    const res = await modulesApi.updateSkillMeta(selected.value.id, skillEditForm.value)
    moduleSkill.value = res.data
    showEditSkillDialog.value = false
    ElMessage.success('已保存')
  } catch (e) { console.error(e) }
  finally { savingSkill.value = false }
}

// ── 文档分类 ──────────────────────────────────────────────────────────────────
const docTypeOrder = ['analysis', 'design', 'api', 'diagram', 'other']

const docsByType = computed(() => {
  const groups: Record<string, any[]> = { analysis: [], design: [], api: [], diagram: [], other: [] }
  for (const doc of moduleDocs.value) {
    const t = (doc.document_type as string) || 'other'
    if (t in groups) groups[t].push(doc)
    else groups.other.push(doc)
  }
  return groups
})

// ── 合并文档 ──────────────────────────────────────────────────────────────────
const showMergeDialog = ref(false)
const mergeForm = ref({ title: '' })
const mergeDocSearch = ref('')
const mergeDocSelected = ref<string[]>([])
const merging = ref(false)

const filterMergeDocs = computed(() => {
  const q = mergeDocSearch.value.trim().toLowerCase()
  const list = moduleDocs.value.filter(d => d.status === 'archived')
  return q ? list.filter(d => d.title.toLowerCase().includes(q)) : list
})

const toggleMergeDoc = (id: string) => {
  const idx = mergeDocSelected.value.indexOf(id)
  if (idx >= 0) mergeDocSelected.value.splice(idx, 1)
  else mergeDocSelected.value.push(id)
}

const openMergeDialog = () => {
  mergeForm.value = { title: `${selected.value?.name || '模块'}设计文档` }
  mergeDocSearch.value = ''
  mergeDocSelected.value = []
  showMergeDialog.value = true
}

const doMerge = async () => {
  if (!selected.value || mergeDocSelected.value.length < 2) return
  merging.value = true
  try {
    const res = await documentsApi.merge({
      title: mergeForm.value.title,
      source_document_ids: [...mergeDocSelected.value],
      module_id: selected.value.id,
    })
    showMergeDialog.value = false
    const dRes = await modulesApi.documents(selected.value.id)
    moduleDocs.value = dRes.data
    ElMessage.success('合并成功')
    openViewDoc(res.data)
  } catch (e) { console.error(e) }
  finally { merging.value = false }
}

// ── 查看文档 ──────────────────────────────────────────────────────────────────
const showViewDoc = ref(false)
const viewingDoc = ref<any>(null)
const viewDocVersions = ref<any[]>([])
const loadingVersions = ref(false)
const viewingVersion = ref<any>(null)

const viewCurrentContent = computed(() => {
  if (viewingVersion.value) return viewingVersion.value.content || ''
  return viewingDoc.value?.content || ''
})

const openViewDoc = async (doc: any) => {
  viewingDoc.value = doc
  viewingVersion.value = null
  viewDocVersions.value = []
  showViewDoc.value = true
  loadingVersions.value = true
  try {
    const res = await documentsApi.versions(doc.id)
    viewDocVersions.value = res.data
  } catch (e) { console.error(e) }
  finally { loadingVersions.value = false }
}

const selectVersion = (ver: any) => {
  viewingVersion.value = viewingVersion.value?.id === ver.id ? null : ver
}

// ── 编辑文档 ──────────────────────────────────────────────────────────────────
const showEditDoc = ref(false)
const editDocForm = ref({ title: '', document_type: 'design', content: '', change_note: '' })
const savingEditDoc = ref(false)
const editingDocId = ref('')

const openEditDoc = (doc: any) => {
  editingDocId.value = doc.id
  editDocForm.value = {
    title: doc.title,
    document_type: doc.document_type || 'design',
    content: doc.content || '',
    change_note: '',
  }
  showEditDoc.value = true
}

const openEditFromView = () => {
  if (!viewingDoc.value) return
  showViewDoc.value = false
  openEditDoc(viewingDoc.value)
}

const saveEditDoc = async () => {
  savingEditDoc.value = true
  try {
    const res = await documentsApi.update(editingDocId.value, {
      title: editDocForm.value.title,
      document_type: editDocForm.value.document_type,
      content: editDocForm.value.content,
      change_note: editDocForm.value.change_note || undefined,
    })
    const idx = moduleDocs.value.findIndex((d: any) => d.id === editingDocId.value)
    if (idx >= 0) moduleDocs.value[idx] = res.data
    showEditDoc.value = false
    ElMessage.success('保存成功')
  } catch (e) { console.error(e) }
  finally { savingEditDoc.value = false }
}

// ── 发布（归档）文档 ──────────────────────────────────────────────────────────
const publishDoc = async (doc: any) => {
  try {
    const res = await documentsApi.archive(doc.id)
    const idx = moduleDocs.value.findIndex((d: any) => d.id === doc.id)
    if (idx >= 0) moduleDocs.value[idx] = res.data
    await syncSkill()
    ElMessage.success('已发布')
  } catch (e) { console.error(e) }
}

// ── 关联已有文档 ──────────────────────────────────────────────────────────────
const showAddDocDialog = ref(false)
const addDocSearch = ref('')
const addDocSelected = ref<string[]>([])
const availableDocs = ref<any[]>([])
const addingDocs = ref(false)

const filteredAvailableDocs = computed(() => {
  const q = addDocSearch.value.trim().toLowerCase()
  return q ? availableDocs.value.filter(d => d.title.toLowerCase().includes(q)) : availableDocs.value
})

const openAddDocDialog = async () => {
  addDocSearch.value = ''
  addDocSelected.value = []
  try {
    const res = await documentsApi.list({ status: 'archived' })
    const alreadyIn = new Set(moduleDocs.value.map((d: any) => d.id))
    availableDocs.value = (res.data as any[]).filter(d => !alreadyIn.has(d.id))
  } catch (e) { console.error(e) }
  showAddDocDialog.value = true
}

const confirmAddDocs = async () => {
  if (!selected.value) return
  addingDocs.value = true
  try {
    await Promise.all(addDocSelected.value.map(docId =>
      documentsApi.update(docId, { module_id: selected.value.id })
    ))
    showAddDocDialog.value = false
    const dRes = await modulesApi.documents(selected.value.id)
    moduleDocs.value = dRes.data
    await syncSkill()
    ElMessage.success('关联成功')
  } catch (e) { console.error(e) }
  finally { addingDocs.value = false }
}

// ── 移除文档 ──────────────────────────────────────────────────────────────────
const removeDoc = async (doc: any) => {
  try {
    await documentsApi.update(doc.id, { module_id: null })
    moduleDocs.value = moduleDocs.value.filter((d: any) => d.id !== doc.id)
    await syncSkill()
    ElMessage.success('已移除')
  } catch (e) { console.error(e) }
}

// ── Skill 同步 ────────────────────────────────────────────────────────────────
const syncSkill = async () => {
  if (!selected.value) return
  try {
    const res = await modulesApi.syncSkill(selected.value.id)
    moduleSkill.value = res.data
  } catch (e) { console.error(e) }
}

// ── 模块树 ────────────────────────────────────────────────────────────────────
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
  moduleDocs.value = dRes.data
  moduleSkill.value = kRes.data.skills?.[0] || null
}

// ── 模块 CRUD ─────────────────────────────────────────────────────────────────
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
    const payload = { ...form.value, parent_id: editing.value?.parent_id || null, project_id: projectStore.currentProjectId }
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

const deleteSkill = async () => {
  if (!selected.value) return
  try {
    await ElMessageBox.confirm(`删除 Skill「${moduleSkill.value?.name}」？`, '确认删除', { type: 'warning', confirmButtonText: '删除', confirmButtonClass: 'el-button--danger' })
    await modulesApi.deleteSkill(selected.value.id)
    moduleSkill.value = null
    ElMessage.success('Skill 已删除')
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

// ── 工具函数 ──────────────────────────────────────────────────────────────────
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'
const docTypeIcon = (t: string) => ({ analysis: '◇', design: '◆', api: '⌬', diagram: '⌖', other: '◦' }[t] || '◦')
const docTypeText = (t: string) => ({ analysis: '需求文档', design: '设计文档', api: 'API 文档', diagram: '架构图', other: '其他' }[t] || t)

const fetchData = async () => {
  try {
    const params = projectStore.currentProjectId ? { project_id: projectStore.currentProjectId } : {}
    const res = await modulesApi.list(params)
    modules.value = res.data
  } catch (e) { console.error(e) }
}

onMounted(fetchData)
</script>

<style scoped>
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; }
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
.module-stats {
  display:flex; align-items:center; gap:0;
  font-size:12.5px; color:#6b7280; margin-top:8px;
}
.module-tabs { margin-top:0; }
.module-tabs .el-tabs__header { margin:0; }

/* 类型分组标题 */
.type-section-header {
  display:flex; align-items:center; gap:8px;
  margin:16px 0 10px; padding:0 2px;
  font-size:13px; font-weight:600; color:#374151;
}
.type-section-label { letter-spacing:.02em; }
.section-count {
  display:inline-flex; align-items:center; justify-content:center;
  min-width:20px; height:20px; padding:0 6px;
  background:#f3f4f6; border-radius:10px;
  font-size:12px; color:#6b7280;
}

/* 文档卡片 */
.doc-cards { display:flex; flex-direction:column; gap:8px; }
.doc-card {
  display:flex; align-items:flex-start; gap:14px;
  padding:12px 16px;
  background:#fff; border:1px solid #e5e7eb; border-radius:10px;
  transition:box-shadow .15s;
}
.doc-card:hover { box-shadow:0 2px 8px rgba(0,0,0,.07); }
.doc-card-icon {
  width:34px; height:34px; border-radius:8px; flex-shrink:0;
  display:flex; align-items:center; justify-content:center;
  font-size:15px; background:#f3f4f6;
}
.doc-card-icon.design { background:#ede9fe; color:#7c3aed; }
.doc-card-icon.analysis { background:#e0e7ff; color:#4338ca; }
.doc-card-icon.api { background:#d1fae5; color:#065f46; }
.doc-card-icon.diagram { background:#fef3c7; color:#92400e; }
.doc-card-icon.other { background:#f3f4f6; color:#6b7280; }
.doc-card-body { flex:1; min-width:0; }
.doc-card-title { font-size:14px; font-weight:600; color:#111827; margin-bottom:5px; }
.doc-card-meta { display:flex; align-items:center; gap:8px; }
.doc-card-version { font-size:12px; color:#9ca3af; }
.doc-card-date { font-size:12px; color:#9ca3af; margin-left:auto; }
.doc-card-summary {
  font-size:12.5px; color:#6b7280; line-height:1.5; margin-top:4px;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
}
.doc-card-actions {
  display:flex; align-items:center; flex-shrink:0; gap:2px;
}

/* 合并文档选择项 */
.merge-doc-item {
  display:flex; align-items:center; gap:10px;
  padding:10px 14px; cursor:pointer;
  border-bottom:1px solid var(--el-border-color-lighter);
  transition:background .1s;
}
.merge-doc-item:hover { background:#f9fafb; }
.merge-doc-item.selected { background:#eef2ff; }
.merge-doc-item:last-child { border-bottom:none; }

/* 版本历史 */
.version-item {
  padding:10px 16px; cursor:pointer; border-bottom:1px solid #f3f4f6;
  transition:background .1s;
}
.version-item:hover { background:#f9fafb; }
.version-item.active { background:#eef2ff; }
.version-num { font-size:13px; font-weight:600; color:#374151; }
.version-date { font-size:12px; color:#9ca3af; }
.version-note { font-size:12px; color:#6b7280; margin-top:3px; }

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
