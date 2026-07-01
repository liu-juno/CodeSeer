<template>
  <div class="settings-page">
    <div class="page-header">
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane name="state-machine">
        <template #label>
          <span style="display:flex; align-items:center; gap:6px;">
            <span>↻</span> 状态机
          </span>
        </template>
        <el-card shadow="never">
          <template #header>
            <div style="display:flex; align-items:center; justify-content:space-between;">
              <div>
                <div style="font-weight:600; margin:0;">需求状态机</div>
                <el-text type="info" class="text-small">配置每个状态允许流转到的目标状态</el-text>
              </div>
              <el-button type="primary" @click="saveStateMachine" :loading="saving">保存</el-button>
            </div>
          </template>
          <el-table :data="stateMachine" stripe size="small">
            <el-table-column prop="state" label="状态" width="140">
              <template #default="{ row }">
                <code>{{ row.state }}</code>
              </template>
            </el-table-column>
            <el-table-column label="名称" width="180">
              <template #default="{ row, $index }">
                <el-input v-model="stateMachine[$index].name" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="允许流转到">
              <template #default="{ row, $index }">
                <div style="display:flex; flex-wrap:wrap; gap:4px; align-items:center;">
                  <el-tag v-for="t in row.allowed_transitions" :key="t" closable size="small" @close="removeTransition($index, t)">
                    {{ t }}
                  </el-tag>
                  <el-select size="small" placeholder="+ 添加" style="width:100px;" @change="(v:string) => addTransition($index, v)">
                    <el-option v-for="other in otherStates(row, $index)" :key="other.state" :label="other.name" :value="other.state" />
                  </el-select>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="类型" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_initial" type="primary" size="small">初始</el-tag>
                <el-tag v-if="row.is_terminal" type="success" size="small">终态</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ $index }">
                <el-button text size="small" @click="moveState($index, -1)">↑</el-button>
                <el-button text size="small" @click="moveState($index, 1)">↓</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane name="llm">
        <template #label>
          <span style="display:flex; align-items:center; gap:6px;">
            <span>⬡</span> AI / LLM
          </span>
        </template>
        <el-card shadow="never" style="margin-bottom:16px;">
          <template #header><div style="font-weight:600;">大模型（AI）配置</div></template>
          <el-form label-position="top" style="max-width:560px;">
            <el-form-item label="Provider">
              <el-select v-model="envForm.LLM_PROVIDER" style="width:100%;">
                <el-option value="openai" label="OpenAI / 兼容 OpenAI API" />
                <el-option value="anthropic" label="Anthropic (Claude)" />
              </el-select>
            </el-form-item>
            <el-form-item label="Base URL">
              <el-input v-model="envForm.LLM_BASE_URL" placeholder="https://api.openai.com/v1" />
            </el-form-item>
            <el-form-item label="API Key">
              <el-input v-model="envForm.LLM_API_KEY" type="password" show-password placeholder="sk-..." />
              <div style="font-size:12px; color:#9ca3af; margin-top:4px;">留空则保持当前值不变；已配置时显示脱敏值</div>
            </el-form-item>
            <el-form-item label="模型">
              <el-input v-model="envForm.LLM_MODEL" placeholder="gpt-4o-mini / claude-3-5-sonnet-20241022" />
            </el-form-item>
            <div style="display:flex; gap:16px;">
              <el-form-item label="Max Tokens" style="flex:1;">
                <el-input-number v-model="envForm.LLM_MAX_TOKENS" :min="100" :max="200000" />
              </el-form-item>
              <el-form-item label="Temperature" style="flex:1;">
                <el-input-number v-model="envForm.LLM_TEMPERATURE" :min="0" :max="2" :step="0.1" :precision="1" />
              </el-form-item>
            </div>
            <div v-if="envForm.LLM_API_KEY && !envForm.LLM_API_KEY.includes('****') && envForm.LLM_API_KEY.length > 10">
              <el-alert type="success" :closable="false">✓ API Key 已配置</el-alert>
            </div>
            <div v-else-if="!envForm.LLM_API_KEY">
              <el-alert type="warning" :closable="false">尚未配置 API Key，文档合并功能将无法使用</el-alert>
            </div>
          </el-form>
        </el-card>

        <el-card shadow="never" style="margin-bottom:16px;">
          <template #header><div style="font-weight:600;">FTP 存储配置</div></template>
          <el-form label-position="top" style="max-width:560px;">
            <el-form-item label="FTP Host">
              <el-input v-model="envForm.FTP_HOST" placeholder="ftp.example.com" />
            </el-form-item>
            <div style="display:flex; gap:12px;">
              <el-form-item label="端口" style="width:120px;">
                <el-input-number v-model="envForm.FTP_PORT" :min="1" :max="65535" />
              </el-form-item>
              <el-form-item label="用户名" style="flex:1;">
                <el-input v-model="envForm.FTP_USERNAME" placeholder="admin" />
              </el-form-item>
              <el-form-item label="密码" style="flex:1;">
                <el-input v-model="envForm.FTP_PASSWORD" type="password" show-password placeholder="••••" />
              </el-form-item>
            </div>
            <el-form-item label="远程路径">
              <el-input v-model="envForm.FTP_REMOTE_BASE_PATH" placeholder="/code-changes" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never">
          <template #header><div style="font-weight:600;">OSS 存储配置（可替代 FTP）</div></template>
          <el-form label-position="top" style="max-width:560px;">
            <el-form-item label="Endpoint">
              <el-input v-model="envForm.OSS_ENDPOINT" placeholder="https://s3.amazonaws.com" />
            </el-form-item>
            <el-form-item label="Access Key ID">
              <el-input v-model="envForm.OSS_ACCESS_KEY_ID" placeholder="AKIA..." />
            </el-form-item>
            <el-form-item label="Access Key Secret">
              <el-input v-model="envForm.OSS_ACCESS_KEY_SECRET" type="password" show-password placeholder="••••" />
            </el-form-item>
            <el-form-item label="Bucket Name">
              <el-input v-model="envForm.OSS_BUCKET_NAME" placeholder="codeseer-changes" />
            </el-form-item>
          </el-form>
        </el-card>

        <div style="margin-top:16px;">
          <el-button type="primary" :loading="savingLlm" @click="saveEnv">保存所有配置</el-button>
        </div>
      </el-tab-pane>

      <el-tab-pane name="custom-fields">
        <template #label>
          <span style="display:flex; align-items:center; gap:6px;">
            <span>◆</span> 自定义字段
          </span>
        </template>
        <el-card shadow="never">
          <template #header>
            <div style="display:flex; align-items:center; justify-content:space-between;">
              <div>
                <div style="font-weight:600; margin:0;">自定义需求字段</div>
                <el-text type="info" class="text-small">为需求表单添加业务专属字段</el-text>
              </div>
              <el-button type="primary" @click="openFieldForm()">
                <el-icon><Plus /></el-icon> 新建字段
              </el-button>
            </div>
          </template>
          <el-table v-if="customFields.length" :data="customFields" stripe size="small">
            <el-table-column prop="field_key" label="字段 Key" width="160">
              <template #default="{ row }"><code>{{ row.field_key }}</code></template>
            </el-table-column>
            <el-table-column prop="field_name" label="显示名" />
            <el-table-column label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ typeLabel(row.field_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="必填" width="80">
              <template #default="{ row }">
                <el-text v-if="row.required" type="danger">必填</el-text>
                <el-text v-else type="info">否</el-text>
              </template>
            </el-table-column>
            <el-table-column label="选项" width="160">
              <template #default="{ row }">
                <el-text type="info">{{ row.options?.length ? row.options.join(', ') : '-' }}</el-text>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button text size="small" type="primary" @click="openFieldForm(row)">编辑</el-button>
                <el-button text size="small" type="danger" @click="deleteField(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="还没有自定义字段" />
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showFieldForm" :title="editingField?.id ? '编辑字段' : '新建字段'" width="480px">
      <el-form :model="fieldForm" label-position="top">
        <el-form-item label="字段 Key" required>
          <el-input v-model="fieldForm.field_key" :disabled="!!editingField?.id" placeholder="英文，唯一标识，如 severity" />
        </el-form-item>
        <el-form-item label="显示名" required>
          <el-input v-model="fieldForm.field_name" placeholder="如：严重等级" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="fieldForm.field_type" style="width:100%;">
            <el-option value="text" label="文本" />
            <el-option value="number" label="数字" />
            <el-option value="date" label="日期" />
            <el-option value="select" label="单选" />
            <el-option value="multiselect" label="多选" />
            <el-option value="user" label="人员" />
            <el-option value="module" label="模块" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="fieldForm.field_type === 'select' || fieldForm.field_type === 'multiselect'" label="选项（每行一个）">
          <el-input v-model="optionsText" type="textarea" :rows="3" placeholder="P0&#10;P1&#10;P2" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="fieldForm.required">必填</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFieldForm = false">取消</el-button>
        <el-button type="primary" :loading="saving" :disabled="!fieldForm.field_key || !fieldForm.field_name" @click="saveField">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { configApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const tabs = [
  { key: 'state-machine', label: '状态机', icon: '↻' },
  { key: 'custom-fields', label: '自定义字段', icon: '◆' },
]
const route = useRoute()
const router = useRouter()
const activeTab = ref<string>((route.query.tab as string) || 'state-machine')

const stateMachine = ref<any[]>([])
const customFields = ref<any[]>([])
const saving = ref(false)
const savingLlm = ref(false)
const showFieldForm = ref(false)
const editingField = ref<any>(null)
const fieldForm = ref({ field_key: '', field_name: '', field_type: 'text', required: false })
const optionsText = ref('')
const envForm = ref<Record<string, any>>({})

const otherStates = (s: any, idx: number) => stateMachine.value.filter((_, i) => i !== idx)

const removeTransition = (idx: number, t: string) => {
  stateMachine.value[idx].allowed_transitions = stateMachine.value[idx].allowed_transitions.filter((x: string) => x !== t)
}
const addTransition = (idx: number, v: string) => {
  if (v && !stateMachine.value[idx].allowed_transitions.includes(v)) {
    stateMachine.value[idx].allowed_transitions.push(v)
  }
}
const moveState = (idx: number, dir: number) => {
  const newIdx = idx + dir
  if (newIdx < 0 || newIdx >= stateMachine.value.length) return
  const [item] = stateMachine.value.splice(idx, 1)
  stateMachine.value.splice(newIdx, 0, item)
}

const typeLabel = (t: string) => ({
  text: '文本', number: '数字', date: '日期',
  select: '单选', multiselect: '多选', user: '人员', module: '模块',
}[t] || t)

const saveStateMachine = async () => {
  saving.value = true
  try {
    const payload = stateMachine.value.map((s, i) => ({
      state: s.state, name: s.name, allowed_transitions: s.allowed_transitions,
      is_initial: s.is_initial, is_terminal: s.is_terminal, order: i,
    }))
    const res = await configApi.updateStateMachine(payload)
    stateMachine.value = res.data
    ElMessage.success('状态机已保存')
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

const openFieldForm = (f?: any) => {
  if (f) {
    editingField.value = f
    fieldForm.value = { field_key: f.field_key, field_name: f.field_name, field_type: f.field_type, required: f.required }
    optionsText.value = (f.options || []).join('\n')
  } else {
    editingField.value = null
    fieldForm.value = { field_key: '', field_name: '', field_type: 'text', required: false }
    optionsText.value = ''
  }
  showFieldForm.value = true
}

const saveField = async () => {
  saving.value = true
  try {
    const options = optionsText.value.split('\n').map(s => s.trim()).filter(Boolean)
    const data = { ...fieldForm.value, options }
    if (editingField.value?.id) {
      await configApi.updateCustomField(editingField.value.id, data)
    } else {
      await configApi.createCustomField(data)
    }
    showFieldForm.value = false
    ElMessage.success('保存成功')
    fetchCustomFields()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

const deleteField = async (f: any) => {
  try {
    await configApi.deleteCustomField(f.id)
    ElMessage.success('删除成功')
    fetchCustomFields()
  } catch (e) { console.error(e) }
}

const fetchStateMachine = async () => {
  const res = await configApi.stateMachine()
  stateMachine.value = res.data
}
const fetchCustomFields = async () => {
  const res = await configApi.customFields()
  customFields.value = res.data
}
const fetchLlmConfig = async () => {
  try {
    const res = await configApi.envConfig()
    envForm.value = res.data
  } catch (e) { console.error(e) }
}
const saveEnv = async () => {
  savingLlm.value = true
  try {
    await configApi.updateEnvConfig(envForm.value)
    ElMessage.success('配置已保存到 .env')
  } catch (e) { console.error(e) }
  finally { savingLlm.value = false }
}

onMounted(() => {
  fetchStateMachine()
  fetchCustomFields()
  fetchLlmConfig()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-title { font-size: 20px; font-weight: 700; color: #1f2329; margin: 0; }
.page-subtitle { font-size: 13px; color: #969ba4; margin: 4px 0 0 0; }
</style>
