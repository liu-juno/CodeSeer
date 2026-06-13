<template>
  <div class="settings-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">系统设置</h1>
        <p class="page-subtitle">配置状态机、自定义字段、平台高级选项</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="settings-tabs">
      <button v-for="tab in tabs" :key="tab.key" :class="['tab-btn', { active: activeTab === tab.key }]" @click="switchTab(tab.key)">
        <span class="tab-icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <!-- State Machine -->
    <div v-if="activeTab === 'state-machine'" class="card">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
        <div>
          <div class="card-title" style="margin-bottom:0">需求状态机</div>
          <p class="text-muted text-small" style="margin-top:4px;">配置每个状态允许流转到的目标状态</p>
        </div>
        <button class="btn btn-primary" @click="saveStateMachine" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
      <table class="table" style="margin:-4px -4px">
        <thead>
          <tr>
            <th style="width:140px">状态</th>
            <th>名称</th>
            <th>允许流转到</th>
            <th style="width:100px">类型</th>
            <th style="width:80px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(s, idx) in stateMachine" :key="s.id || s.state">
            <td><code class="text-small">{{ s.state }}</code></td>
            <td>
              <input v-model="s.name" class="form-input form-input-sm" />
            </td>
            <td>
              <div class="transition-tags">
                <span v-for="t in s.allowed_transitions" :key="t" class="transition-tag">
                  {{ t }} <button @click="removeTransition(idx, t)">×</button>
                </span>
                <select @change="addTransition(idx, $event)" class="form-input form-input-sm" style="width:auto; padding:2px 6px;">
                  <option value="">+ 添加</option>
                  <option v-for="other in otherStates(s, idx)" :key="other.state" :value="other.state">{{ other.name }}</option>
                </select>
              </div>
            </td>
            <td>
              <span v-if="s.is_initial" class="badge blue">初始</span>
              <span v-if="s.is_terminal" class="badge green">终态</span>
            </td>
            <td>
              <button class="btn-link" @click="moveState(idx, -1)">↑</button>
              <button class="btn-link" @click="moveState(idx, 1)">↓</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Custom Fields -->
    <div v-if="activeTab === 'custom-fields'" class="card">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
        <div>
          <div class="card-title" style="margin-bottom:0">自定义需求字段</div>
          <p class="text-muted text-small" style="margin-top:4px;">为需求表单添加业务专属字段</p>
        </div>
        <button class="btn btn-primary" @click="openFieldForm()">
          <span>＋</span> 新建字段
        </button>
      </div>
      <table v-if="customFields.length" class="table" style="margin:-4px -4px">
        <thead>
          <tr>
            <th>字段 Key</th>
            <th>显示名</th>
            <th>类型</th>
            <th>必填</th>
            <th>选项</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in customFields" :key="f.id">
            <td><code class="text-small">{{ f.field_key }}</code></td>
            <td style="font-weight:500;">{{ f.field_name }}</td>
            <td><span class="type-pill">{{ typeLabel(f.field_type) }}</span></td>
            <td>
              <span v-if="f.required" class="text-small" style="color:#dc2626;">必填</span>
              <span v-else class="text-small text-muted">否</span>
            </td>
            <td class="text-muted text-small">
              {{ f.options?.length ? f.options.join(', ') : '-' }}
            </td>
            <td>
              <button class="btn-link" @click="openFieldForm(f)">编辑</button>
              <button class="btn-link danger" @click="deleteField(f)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state" style="padding:32px 0">
        <div class="empty-state-icon">◆</div>
        <div class="empty-state-text">还没有自定义字段</div>
      </div>
    </div>

    <!-- Field Form Modal -->
    <div v-if="showFieldForm" class="modal-overlay" @click.self="showFieldForm = false">
      <div class="modal" style="width:480px;">
        <div class="modal-header">
          <h3>{{ editingField?.id ? '编辑字段' : '新建字段' }}</h3>
          <button class="modal-close" @click="showFieldForm = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">字段 Key <span class="required">*</span></label>
            <input v-model="fieldForm.field_key" class="form-input" :disabled="!!editingField?.id" placeholder="英文，唯一标识，如 severity" />
          </div>
          <div class="form-group">
            <label class="form-label">显示名 <span class="required">*</span></label>
            <input v-model="fieldForm.field_name" class="form-input" placeholder="如：严重等级" />
          </div>
          <div class="form-group">
            <label class="form-label">类型</label>
            <select v-model="fieldForm.field_type" class="form-input">
              <option value="text">文本</option>
              <option value="number">数字</option>
              <option value="date">日期</option>
              <option value="select">单选</option>
              <option value="multiselect">多选</option>
              <option value="user">人员</option>
              <option value="module">模块</option>
            </select>
          </div>
          <div v-if="fieldForm.field_type === 'select' || fieldForm.field_type === 'multiselect'" class="form-group">
            <label class="form-label">选项（每行一个）</label>
            <textarea v-model="optionsText" class="form-input" style="min-height:80px;" placeholder="P0&#10;P1&#10;P2"></textarea>
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
              <input type="checkbox" v-model="fieldForm.required" />
              <span style="font-size:13.5px;">必填</span>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showFieldForm = false">取消</button>
          <button class="btn btn-primary" :disabled="!fieldForm.field_key || !fieldForm.field_name || saving" @click="saveField">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { configApi } from '@/api'

const tabs = [
  { key: 'state-machine', label: '状态机', icon: '↻' },
  { key: 'custom-fields', label: '自定义字段', icon: '◆' },
]
const route = useRoute()
const router = useRouter()
const activeTab = ref<string>((route.query.tab as string) || 'state-machine')

const switchTab = (key: string) => {
  activeTab.value = key
  router.replace({ query: { ...route.query, tab: key } })
}

const stateMachine = ref<any[]>([])
const customFields = ref<any[]>([])
const saving = ref(false)
const showFieldForm = ref(false)
const editingField = ref<any>(null)
const fieldForm = ref({ field_key: '', field_name: '', field_type: 'text', required: false })
const optionsText = ref('')

const otherStates = (s: any, idx: number) => stateMachine.value.filter((o, i) => i !== idx)

const removeTransition = (idx: number, t: string) => {
  stateMachine.value[idx].allowed_transitions = stateMachine.value[idx].allowed_transitions.filter((x: string) => x !== t)
}
const addTransition = (idx: number, ev: any) => {
  const v = ev.target.value
  if (v && !stateMachine.value[idx].allowed_transitions.includes(v)) {
    stateMachine.value[idx].allowed_transitions.push(v)
  }
  ev.target.value = ''
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
    alert('状态机已保存')
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
    fetchCustomFields()
  } catch (e: any) { alert(e?.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

const deleteField = async (f: any) => {
  if (!confirm(`删除字段「${f.field_name}」？`)) return
  await configApi.deleteCustomField(f.id)
  fetchCustomFields()
}

const fetchStateMachine = async () => {
  const res = await configApi.stateMachine()
  stateMachine.value = res.data
}
const fetchCustomFields = async () => {
  const res = await configApi.customFields()
  customFields.value = res.data
}

onMounted(() => {
  fetchStateMachine()
  fetchCustomFields()
})
</script>

<style scoped>
.settings-tabs {
  display: flex; gap: 4px; margin-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}
.settings-tabs .tab-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 16px; background: none; border: none;
  border-bottom: 2px solid transparent;
  color: #6b7280; font-size: 13.5px; font-weight: 500;
  cursor: pointer; transition: all 0.15s;
}
.settings-tabs .tab-btn:hover { color: #374151; }
.settings-tabs .tab-btn.active { color: #6366f1; border-bottom-color: #6366f1; }
.tab-icon { font-size: 14px; }

.form-input-sm { padding: 4px 8px; font-size: 12.5px; height: auto; }

.transition-tags { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
.transition-tag {
  font-family: monospace; font-size: 11px;
  background: #eef2ff; color: #4338ca;
  padding: 2px 4px 2px 8px; border-radius: 4px;
  display: flex; align-items: center; gap: 2px;
}
.transition-tag button {
  background: none; border: none; cursor: pointer;
  color: #6366f1; padding: 0 2px; font-size: 13px; line-height: 1;
}
.transition-tag button:hover { color: #dc2626; }

.badge {
  font-size: 11px; font-weight: 500;
  padding: 1px 6px; border-radius: 4px;
}
.badge.blue   { background: #dbeafe; color: #1e40af; }
.badge.green  { background: #d1fae5; color: #065f46; }

.type-pill {
  font-size: 12px; font-weight: 500;
  background: #f3f4f6; color: #374151;
  padding: 2px 8px; border-radius: 4px;
}

.btn-link {
  background: none; border: none; cursor: pointer;
  color: #6366f1; font-size: 13px; padding: 0 4px;
}
.btn-link:hover { text-decoration: underline; }
.btn-link.danger { color: #dc2626; }
</style>
