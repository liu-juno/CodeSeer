<template>
  <div class="webhooks-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Webhook 配置</h1>
        <p class="page-subtitle">订阅平台事件，外部系统自动接收通知</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <span>＋</span> 新建 Webhook
      </button>
    </div>

    <div class="card" style="padding:0; overflow:hidden;">
      <div v-if="loading" class="empty-state"><div class="empty-state-text text-muted">加载中...</div></div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>名称</th>
            <th>URL</th>
            <th>订阅事件</th>
            <th>状态</th>
            <th>最近投递</th>
            <th style="width:220px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="wh in webhooks" :key="wh.id">
            <td style="font-weight:600;">{{ wh.name }}</td>
            <td class="text-muted text-small" style="font-family:monospace; max-width:280px; overflow:hidden; text-overflow:ellipsis;">{{ wh.url }}</td>
            <td>
              <div class="event-tags">
                <span v-for="ev in parseEvents(wh.events)" :key="ev" class="event-tag">{{ ev }}</span>
              </div>
            </td>
            <td>
              <span :class="['status-badge', wh.enabled ? 'active' : 'inactive']">
                {{ wh.enabled ? '启用' : '禁用' }}
              </span>
            </td>
            <td class="text-muted text-small">{{ lastDelivery(wh.id) }}</td>
            <td>
              <div class="action-row">
                <button class="btn-link" @click="testWebhook(wh)">测试</button>
                <button class="btn-link" @click="openEdit(wh)">编辑</button>
                <button class="btn-link" @click="viewDeliveries(wh)">投递</button>
                <button class="btn-link danger" @click="deleteWebhook(wh)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="webhooks.length === 0">
            <td colspan="6">
              <div class="empty-state">
                <div class="empty-state-icon">⌬</div>
                <div class="empty-state-text">还没有 Webhook，点击「新建」开始</div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Edit/Create Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal" style="width:540px;">
        <div class="modal-header">
          <h3>{{ editing ? '编辑 Webhook' : '新建 Webhook' }}</h3>
          <button class="modal-close" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">名称 <span class="required">*</span></label>
            <input v-model="form.name" class="form-input" placeholder="如：飞书通知机器人" />
          </div>
          <div class="form-group">
            <label class="form-label">URL <span class="required">*</span></label>
            <input v-model="form.url" class="form-input" placeholder="https://example.com/webhook" />
          </div>
          <div class="form-group">
            <label class="form-label">签名密钥（可选）</label>
            <input v-model="form.secret" class="form-input" placeholder="用于 HMAC-SHA256 签名验证" />
            <p class="form-hint">平台会以 <code>X-CodeSeer-Signature: sha256=...</code> 头发送签名</p>
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label class="form-label">订阅事件</label>
            <div class="event-pills">
              <label v-for="ev in availableEvents" :key="ev.name" :class="['event-pill', { selected: form.events.includes(ev.name) }]">
                <input type="checkbox" v-model="form.events" :value="ev.name" style="display:none" />
                <span class="pill-name">{{ ev.name }}</span>
                <span class="pill-desc">{{ ev.desc }}</span>
              </label>
            </div>
          </div>
          <div class="form-group" style="margin-top:14px; margin-bottom:0">
            <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
              <input type="checkbox" v-model="form.enabled" />
              <span style="font-size:13.5px;">启用</span>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeForm">取消</button>
          <button class="btn btn-primary" :disabled="!form.name.trim() || !form.url.trim() || saving" @click="saveWebhook">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Deliveries Modal -->
    <div v-if="showDeliveries" class="modal-overlay" @click.self="showDeliveries = false">
      <div class="modal" style="width:720px; max-width:95vw;">
        <div class="modal-header">
          <h3>投递记录 - {{ selectedWh?.name }}</h3>
          <button class="modal-close" @click="showDeliveries = false">✕</button>
        </div>
        <div class="modal-body">
          <table v-if="deliveries.length" class="table" style="margin:-4px -4px">
            <thead>
              <tr><th>事件</th><th>响应</th><th>结果</th><th>时间</th></tr>
            </thead>
            <tbody>
              <tr v-for="d in deliveries" :key="d.id">
                <td><code class="text-small">{{ d.event }}</code></td>
                <td class="text-small">{{ d.response_status || '-' }}</td>
                <td>
                  <span :class="['test-result', d.success ? 'all_passed' : 'failed']">
                    {{ d.success ? '成功' : '失败' }}
                  </span>
                </td>
                <td class="text-muted text-small">{{ formatDateTime(d.created_at) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state"><div class="empty-state-text text-muted">暂无投递记录</div></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { webhooksApi } from '@/api'

const webhooks = ref<any[]>([])
const deliveries = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const showDeliveries = ref(false)
const editing = ref<any>(null)
const selectedWh = ref<any>(null)
const lastDeliveryMap = ref<Record<string, string>>({})

const form = ref({
  name: '', url: '', secret: '', events: [] as string[], enabled: true,
})

const availableEvents = [
  { name: 'requirement.created', desc: '需求创建' },
  { name: 'requirement.status_changed', desc: '需求状态变更' },
  { name: 'requirement.assigned', desc: '需求指派' },
  { name: 'document.submitted', desc: '文档提交' },
  { name: 'document.archived', desc: '文档归档' },
  { name: 'iteration.released', desc: '迭代发布' },
  { name: 'test.submitted', desc: '测试结果' },
  { name: '*', desc: '所有事件' },
]

const parseEvents = (raw: string) => {
  if (!raw) return []
  try { return JSON.parse(raw) } catch { return [] }
}

const lastDelivery = (id: string) => lastDeliveryMap.value[id] || '-'

const formatDateTime = (d: string) => d ? new Date(d).toLocaleString('zh-CN') : '-'

const openCreate = () => {
  editing.value = null
  form.value = { name: '', url: '', secret: '', events: [], enabled: true }
  showForm.value = true
}

const openEdit = (wh: any) => {
  editing.value = wh
  form.value = {
    name: wh.name, url: wh.url, secret: wh.secret || '',
    events: parseEvents(wh.events), enabled: wh.enabled,
  }
  showForm.value = true
}

const closeForm = () => { showForm.value = false }

const saveWebhook = async () => {
  saving.value = true
  try {
    if (editing.value) {
      await webhooksApi.update(editing.value.id, form.value)
    } else {
      await webhooksApi.create(form.value)
    }
    closeForm()
    fetchData()
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

const testWebhook = async (wh: any) => {
  try {
    await webhooksApi.test(wh.id)
    alert('测试事件已发送，请查看投递记录')
    setTimeout(() => viewDeliveries(wh), 500)
  } catch (e: any) { alert(e?.response?.data?.detail || '发送失败') }
}

const viewDeliveries = async (wh: any) => {
  selectedWh.value = wh
  showDeliveries.value = true
  try {
    const res = await webhooksApi.deliveries(wh.id)
    deliveries.value = res.data
    if (res.data.length) {
      lastDeliveryMap.value[wh.id] = formatDateTime(res.data[0].created_at)
    }
  } catch (e) { console.error(e) }
}

const deleteWebhook = async (wh: any) => {
  if (!confirm(`删除 Webhook「${wh.name}」？`)) return
  try {
    await webhooksApi.delete(wh.id)
    fetchData()
  } catch (e) { console.error(e) }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await webhooksApi.list()
    webhooks.value = res.data
    // load last delivery for each
    for (const wh of res.data) {
      const dRes = await webhooksApi.deliveries(wh.id)
      if (dRes.data.length) {
        lastDeliveryMap.value[wh.id] = formatDateTime(dRes.data[0].created_at)
      }
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.event-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.event-tag {
  font-family: monospace; font-size: 11px;
  background: #eef2ff; color: #4338ca;
  padding: 2px 6px; border-radius: 4px;
}

.action-row { display: flex; gap: 12px; }
.btn-link {
  background: none; border: none; cursor: pointer;
  color: #6366f1; font-size: 13px; padding: 0;
}
.btn-link:hover { text-decoration: underline; }
.btn-link.danger { color: #dc2626; }

.event-pills {
  display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
}
.event-pill {
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px 10px; border: 1px solid #e5e7eb;
  border-radius: 6px; cursor: pointer;
  transition: all 0.1s;
}
.event-pill:hover { border-color: #c7d2fe; }
.event-pill.selected {
  background: #eef2ff; border-color: #6366f1;
}
.pill-name { font-size: 12.5px; font-weight: 600; color: #111827; font-family: monospace; }
.pill-desc { font-size: 11px; color: #6b7280; }

.status-badge.active   { background: #d1fae5; color: #065f46; }
.status-badge.inactive { background: #f3f4f6; color: #6b7280; }
</style>
