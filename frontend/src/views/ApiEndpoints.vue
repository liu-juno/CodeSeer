<template>
  <div class="api-page">
    <div class="page-header">
      <div class="header-left">
        <el-input v-model="search" placeholder="搜索接口 path / 描述..." style="width:220px;" clearable @input="fetchData" />
        <el-select v-model="filterMethod" placeholder="全部方法" style="width:110px;" clearable @change="fetchData">
          <el-option value="GET" label="GET" />
          <el-option value="POST" label="POST" />
          <el-option value="PUT" label="PUT" />
          <el-option value="DELETE" label="DELETE" />
          <el-option value="PATCH" label="PATCH" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="全部状态" style="width:120px;" clearable @change="fetchData">
          <el-option value="draft" label="草稿" />
          <el-option value="published" label="已发布" />
          <el-option value="deprecated" label="已废弃" />
        </el-select>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon> 新增接口
      </el-button>
    </div>

    <el-card shadow="never" body-style="padding:0;">
      <el-table v-loading="loading" :data="endpoints" stripe>
        <el-table-column label="接口" min-width="280">
          <template #default="{ row }">
            <div style="display:flex; align-items:center; gap:10px;">
              <span :class="['method-badge', row.method.toLowerCase()]">{{ row.method }}</span>
              <div>
                <div style="font-weight:600; font-size:13.5px; color:#111827; font-family:monospace;">{{ row.path }}</div>
                <el-text v-if="row.summary" type="info" size="small">{{ row.summary }}</el-text>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="模块" width="140">
          <template #default="{ row }">
            <span v-if="row.module_id" style="font-size:12.5px; color:#6b7280;">{{ getModuleName(row.module_id) }}</span>
            <span v-else style="color:#d1d5db;">—</span>
          </template>
        </el-table-column>
        <el-table-column label="版本" width="80">
          <template #default="{ row }">v{{ row.version }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="120">
          <template #default="{ row }">
            <el-text type="info" size="small">{{ formatDate(row.updated_at) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="right">
          <template #default="{ row }">
            <el-button text size="small" @click="openView(row)">查看</el-button>
            <el-button text size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button text size="small" type="danger" @click="deleteRow(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 环境管理 -->
    <el-card shadow="never" style="margin-top:20px;">
      <template #header>
        <div style="display:flex; align-items:center; justify-content:space-between;">
          <span style="font-weight:600;">测试环境</span>
          <el-button size="small" @click="openEnvForm(null)">+ 添加环境</el-button>
        </div>
      </template>
      <el-empty v-if="environments.length === 0" description="暂无测试环境，点击添加" />
      <div v-else style="display:flex; flex-direction:column; gap:8px;">
        <div v-for="e in environments" :key="e.id" style="display:flex; align-items:center; gap:12px; padding:8px 12px; border:1px solid #e5e7eb; border-radius:8px;">
          <div style="flex:1; min-width:0;">
            <div style="font-weight:600; font-size:13.5px; color:#111827;">{{ e.name }}</div>
            <el-text type="info" size="small">{{ e.base_url }}</el-text>
            <el-tag v-if="e.is_default" size="small" type="success" style="margin-left:8px;">默认</el-tag>
          </div>
          <el-button text size="small" type="primary" @click="openEnvForm(e)">编辑</el-button>
          <el-button text size="small" type="danger" @click="deleteEnv(e)">删除</el-button>
        </div>
      </div>
    </el-card>

    <!-- 新增/编辑接口 dialog -->
    <el-dialog v-model="showForm" :title="editing?.id ? '编辑接口' : '新增接口'" width="720px" destroy-on-close>
      <el-form :model="form" label-position="top">
        <div style="display:flex; gap:12px;">
          <el-form-item label="请求方法" required style="width:120px;">
            <el-select v-model="form.method">
              <el-option value="GET" label="GET" />
              <el-option value="POST" label="POST" />
              <el-option value="PUT" label="PUT" />
              <el-option value="DELETE" label="DELETE" />
              <el-option value="PATCH" label="PATCH" />
            </el-select>
          </el-form-item>
          <el-form-item label="接口路径" required style="flex:1;">
            <el-input v-model="form.path" placeholder="/api/v1/users" />
          </el-form-item>
        </div>
        <div style="display:flex; gap:12px;">
          <el-form-item label="接口描述" style="flex:1;">
            <el-input v-model="form.summary" placeholder="简短描述接口用途" />
          </el-form-item>
          <el-form-item label="所属模块" style="width:180px;">
            <el-select v-model="form.module_id" clearable placeholder="选择模块">
              <el-option v-for="m in modules" :key="m.id" :label="m.name" :value="m.id" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="详细说明">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="接口的详细说明..." />
        </el-form-item>
        <el-form-item label="请求参数 Schema（JSON）">
          <el-input v-model="form.request_schema" type="textarea" :rows="4" placeholder='{"name": "string", "page": 1}' style="font-family:monospace; font-size:12px;" />
        </el-form-item>
        <el-form-item label="响应 Schema（JSON）">
          <el-input v-model="form.response_schema" type="textarea" :rows="4" placeholder='{"code": 0, "data": {...}}' style="font-family:monospace; font-size:12px;" />
        </el-form-item>
        <el-form-item label="公共 Header（JSON，可选）">
          <el-input v-model="form.headers" type="textarea" :rows="2" placeholder='{"Authorization": "Bearer xxx"}' style="font-family:monospace; font-size:12px;" />
        </el-form-item>
        <el-form-item v-if="editing?.id" label="变更说明">
          <el-input v-model="form.change_note" placeholder="简要描述此次修改..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEndpoint">{{ editing?.id ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>

    <!-- 查看接口 dialog -->
    <el-dialog v-model="showView" :title="viewing ? `${viewing.method} ${viewing.path}` : ''" width="900px" destroy-on-close>
      <div v-if="viewing" style="display:flex; gap:16px; min-height:500px;">
        <div style="flex:1; min-width:0;">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
            <span :class="['method-badge', viewing.method.toLowerCase()]">{{ viewing.method }}</span>
            <code style="font-size:14px; font-family:monospace;">{{ viewing.path }}</code>
          </div>
          <el-descriptions :column="2" border size="small" style="margin-bottom:16px;">
            <el-descriptions-item label="描述">{{ viewing.summary || '—' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag size="small" :type="statusType(viewing.status)">{{ statusText(viewing.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="版本">v{{ viewing.version }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatDate(viewing.updated_at) }}</el-descriptions-item>
          </el-descriptions>
          <el-tabs>
            <el-tab-pane label="请求参数">
              <pre class="schema-block">{{ viewing.request_schema || '{}' }}</pre>
            </el-tab-pane>
            <el-tab-pane label="响应参数">
              <pre class="schema-block">{{ viewing.response_schema || '{}' }}</pre>
            </el-tab-pane>
            <el-tab-pane label="Headers">
              <pre class="schema-block">{{ viewing.headers || '{}' }}</pre>
            </el-tab-pane>
          </el-tabs>
          <div style="margin-top:16px;">
            <el-button type="primary" size="small" @click="openTest(viewing)">在线测试</el-button>
            <el-button size="small" @click="openEdit(viewing)">编辑</el-button>
          </div>
        </div>
        <div style="width:240px; flex-shrink:0; border:1px solid var(--el-border-color); border-radius:8px; overflow:hidden;">
          <div style="padding:10px 16px; border-bottom:1px solid var(--el-border-color); background:#fafafa; font-size:13px; font-weight:600; color:#374151;">版本历史</div>
          <div style="max-height:560px; overflow-y:auto;">
            <el-skeleton v-if="loadingVersions" :rows="3" animated style="padding:12px;" />
            <template v-else>
              <div v-if="versions.length === 0" style="padding:20px; text-align:center; color:#9ca3af; font-size:13px;">暂无版本记录</div>
              <div v-for="ver in versions" :key="ver.id" style="padding:10px 16px; border-bottom:1px solid #f3f4f6;">
                <div style="display:flex; align-items:center; justify-content:space-between;">
                  <span style="font-size:13px; font-weight:600; color:#374151;">v{{ ver.version }}</span>
                  <span style="font-size:11px; color:#9ca3af;">{{ formatDate(ver.created_at) }}</span>
                </div>
                <div v-if="ver.change_note" style="font-size:12px; color:#6b7280; margin-top:3px;">{{ ver.change_note }}</div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 在线测试 dialog -->
    <el-dialog v-model="showTest" :title="testEndpoint ? `测试：${testEndpoint.method} ${testEndpoint.path}` : ''" width="800px" destroy-on-close>
      <div v-if="testEndpoint" style="display:flex; flex-direction:column; gap:16px;">
        <div style="display:flex; gap:12px; align-items:center;">
          <span style="font-weight:600; color:#374151;">环境：</span>
          <el-select v-model="testEnvId" placeholder="选择环境" style="flex:1;" @change="loadEnvVariables">
            <el-option v-for="e in environments" :key="e.id" :label="`${e.name} (${e.base_url})`" :value="e.id" />
          </el-select>
        </div>
        <div v-if="testEnvVariables" style="font-size:12px; color:#6b7280; background:#f9fafb; padding:8px 12px; border-radius:6px;">
          <strong>环境变量：</strong>{{ testEnvVariables }}
        </div>
        <el-form-item label="请求参数（JSON）">
          <el-input v-model="testParams" type="textarea" :rows="5" placeholder='{"name": "test"}' style="font-family:monospace; font-size:13px;" />
        </el-form-item>
        <div>
          <el-button type="primary" :loading="testing" :disabled="!testEnvId" @click="doTest">发送请求</el-button>
        </div>
        <div v-if="testResult">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
            <el-tag :type="resultTagType">{{ resultLabel }}</el-tag>
            <span style="font-size:13px; color:#374151;">{{ testResult.status_code }}</span>
            <span style="font-size:12px; color:#9ca3af; margin-left:auto;">耗时 {{ testResult.elapsed_ms }} ms</span>
          </div>
          <div style="background:#1e1e2e; border-radius:8px; padding:16px; max-height:300px; overflow:auto;">
            <pre style="margin:0; font-family:monospace; font-size:12px; color:#cdd6f4; white-space:pre-wrap; word-break:break-all;">{{ testResult.body }}</pre>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 环境表单 dialog -->
    <el-dialog v-model="showEnvForm" :title="editingEnv?.id ? '编辑环境' : '新增环境'" width="480px">
      <el-form :model="envForm" label-position="top">
        <el-form-item label="环境名称" required>
          <el-input v-model="envForm.name" placeholder="如：开发环境" />
        </el-form-item>
        <el-form-item label="Base URL" required>
          <el-input v-model="envForm.base_url" placeholder="https://api-dev.example.com" />
        </el-form-item>
        <el-form-item label="环境变量（JSON，可选）">
          <el-input v-model="envForm.variables" type="textarea" :rows="3" placeholder='{"token": "xxx"}' style="font-family:monospace; font-size:12px;" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="envForm.is_default">设为默认环境</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEnvForm = false">取消</el-button>
        <el-button type="primary" :loading="savingEnv" @click="saveEnv">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiEndpointsApi, modulesApi } from '@/api'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const projectStore = useProjectStore()

const endpoints = ref<any[]>([])
const environments = ref<any[]>([])
const modules = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const filterMethod = ref('')
const filterStatus = ref('')

// Endpoint form
const showForm = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const form = ref({
  method: 'GET', path: '', summary: '', description: '',
  request_schema: '', response_schema: '', headers: '', module_id: '', change_note: ''
})

// View
const showView = ref(false)
const viewing = ref<any>(null)
const versions = ref<any[]>([])
const loadingVersions = ref(false)

// Test
const showTest = ref(false)
const testEndpoint = ref<any>(null)
const testEnvId = ref('')
const testEnvVariables = ref('')
const testParams = ref('')
const testing = ref(false)
const testResult = ref<any>(null)

// Env form
const showEnvForm = ref(false)
const editingEnv = ref<any>(null)
const savingEnv = ref(false)
const envForm = ref({ name: '', base_url: '', variables: '', is_default: false })

const statusType = (s: string) => ({ draft: 'info', published: 'success', deprecated: 'warning' }[s] || 'info')
const statusText = (s: string) => ({ draft: '草稿', published: '已发布', deprecated: '已废弃' }[s] || s)
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'

const resultTagType = computed(() => {
  if (!testResult.value) return 'info'
  return testResult.value.result === 'pass' ? 'success' : testResult.value.result === 'fail' ? 'danger' : 'warning'
})
const resultLabel = computed(() => {
  if (!testResult.value) return ''
  return testResult.value.result === 'pass' ? '✓ 通过' : testResult.value.result === 'fail' ? '✗ 失败' : '⚠ 错误'
})

const getModuleName = (id: string) => modules.value.find(m => m.id === id)?.name || id

const flattenModules = (tree: any[]): any[] => {
  const out: any[] = []
  const walk = (list: any[]) => { for (const m of list) { out.push(m); if (m.children?.length) walk(m.children) } }
  walk(tree)
  return out
}

const fetchData = async () => {
  if (!projectStore.currentProjectId) return
  loading.value = true
  try {
    const [eRes, envRes, mRes] = await Promise.all([
      apiEndpointsApi.list(projectStore.currentProjectId, {
        method: filterMethod.value || undefined,
        status: filterStatus.value || undefined,
        search: search.value || undefined,
      }),
      apiEndpointsApi.listEnvironments(projectStore.currentProjectId),
      modulesApi.list(projectStore.currentProjectId ? { project_id: projectStore.currentProjectId } : {}),
    ])
    endpoints.value = eRes.data
    environments.value = envRes.data
    modules.value = flattenModules(mRes.data)
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const openCreate = () => {
  editing.value = null
  form.value = { method: 'GET', path: '', summary: '', description: '', request_schema: '', response_schema: '', headers: '', module_id: '', change_note: '' }
  showForm.value = true
}

const openEdit = (row: any) => {
  showView.value = false
  editing.value = row
  form.value = { method: row.method, path: row.path, summary: row.summary || '', description: row.description || '', request_schema: row.request_schema || '', response_schema: row.response_schema || '', headers: row.headers || '', module_id: row.module_id || '', change_note: '' }
  showForm.value = true
}

const openView = async (row: any) => {
  viewing.value = row
  versions.value = []
  loadingVersions.value = true
  showView.value = true
  try {
    const res = await apiEndpointsApi.versions(row.id)
    versions.value = res.data
  } catch (e) { console.error(e) }
  finally { loadingVersions.value = false }
}

const openTest = (row: any) => {
  showView.value = false
  testEndpoint.value = row
  testEnvId.value = environments.value.find(e => e.is_default)?.id || environments.value[0]?.id || ''
  testEnvVariables.value = ''
  testParams.value = row.request_schema || ''
  testResult.value = null
  loadEnvVariables()
  showTest.value = true
}

const loadEnvVariables = () => {
  const env = environments.value.find(e => e.id === testEnvId.value)
  testEnvVariables.value = env?.variables || ''
}

const doTest = async () => {
  if (!testEndpoint.value || !testEnvId.value) return
  testing.value = true
  testResult.value = null
  try {
    const res = await apiEndpointsApi.test(testEndpoint.value.id, {
      environment_id: testEnvId.value,
      request_params: testParams.value || undefined,
    })
    testResult.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '请求失败')
  } finally { testing.value = false }
}

const saveEndpoint = async () => {
  saving.value = true
  try {
    if (editing.value?.id) {
      await apiEndpointsApi.update(editing.value.id, form.value)
      ElMessage.success('保存成功')
    } else {
      await apiEndpointsApi.create({ project_id: projectStore.currentProjectId, ...form.value })
      ElMessage.success('创建成功')
    }
    showForm.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

const deleteRow = async (row: any) => {
  try {
    await ElMessageBox.confirm(`删除接口 ${row.method} ${row.path}？`, '确认', { type: 'warning' })
    await apiEndpointsApi.delete(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e?.response?.data?.detail || '删除失败') }
}

// Env
const openEnvForm = (e: any) => {
  editingEnv.value = e
  envForm.value = e ? { name: e.name, base_url: e.base_url, variables: e.variables || '', is_default: e.is_default } : { name: '', base_url: '', variables: '', is_default: false }
  showEnvForm.value = true
}

const saveEnv = async () => {
  savingEnv.value = true
  try {
    if (editingEnv.value?.id) {
      await apiEndpointsApi.updateEnvironment(editingEnv.value.id, envForm.value)
    } else {
      await apiEndpointsApi.createEnvironment({ project_id: projectStore.currentProjectId, ...envForm.value })
    }
    showEnvForm.value = false
    const envRes = await apiEndpointsApi.listEnvironments(projectStore.currentProjectId!)
    environments.value = envRes.data
    ElMessage.success('保存成功')
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '保存失败') }
  finally { savingEnv.value = false }
}

const deleteEnv = async (e: any) => {
  try {
    await ElMessageBox.confirm(`删除环境「${e.name}」？`, '确认', { type: 'warning' })
    await apiEndpointsApi.deleteEnvironment(e.id)
    environments.value = environments.value.filter(env => env.id !== e.id)
    ElMessage.success('已删除')
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e?.response?.data?.detail || '删除失败') }
}

onMounted(fetchData)
</script>

<style scoped>
.api-page { width: 100%; }
.page-header {
  display:flex; align-items:center; justify-content:space-between;
  margin-bottom:20px; flex-wrap:wrap; gap:10px;
}
.header-left { display:flex; align-items:center; gap:10px; }

.method-badge {
  display:inline-block; min-width:52px; text-align:center;
  padding:2px 6px; border-radius:4px; font-size:11px; font-weight:700; font-family:monospace;
}
.method-badge.get { background:#d1fae5; color:#065f46; }
.method-badge.post { background:#fef3c7; color:#92400e; }
.method-badge.put { background:#dbeafe; color:#1e40af; }
.method-badge.delete { background:#fee2e2; color:#991b1b; }
.method-badge.patch { background:#ede9fe; color:#5b21b6; }

.schema-block {
  margin:0; padding:12px; background:#f9fafb; border-radius:6px;
  font-family:monospace; font-size:12px; color:#374151; line-height:1.6; max-height:250px; overflow:auto;
}
</style>
