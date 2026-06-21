<template>
  <div class="webhooks-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Webhook 配置</h1>
        <p class="page-subtitle">订阅平台事件，外部系统自动接收通知</p>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon> 新建 Webhook
      </el-button>
    </div>

    <el-card shadow="never" body-style="padding:0;">
      <el-table v-loading="loading" :data="webhooks" stripe>
        <el-table-column prop="name" label="名称" min-width="150">
          <template #default="{ row }">
            <span style="font-weight:600;">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="URL" min-width="200">
          <template #default="{ row }">
            <el-text type="info" style="font-family:monospace; max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; display:block;">{{ row.url }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="订阅事件" min-width="200">
          <template #default="{ row }">
            <div style="display:flex; flex-wrap:wrap; gap:4px;">
              <el-tag v-for="ev in parseEvents(row.events)" :key="ev" size="small">{{ ev }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">{{ row.enabled ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最近投递" width="120">
          <template #default="{ row }">
            <el-text type="info" size="small">{{ lastDelivery(row.id) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="right">
          <template #default="{ row }">
            <el-button text size="small" type="primary" @click="testWebhook(row)">测试</el-button>
            <el-button text size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button text size="small" type="primary" @click="viewDeliveries(row)">投递</el-button>
            <el-button text size="small" type="danger" @click="deleteWebhook(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showForm" :title="editing ? '编辑 Webhook' : '新建 Webhook'" width="540px">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="如：飞书通知机器人" />
        </el-form-item>
        <el-form-item label="URL" required>
          <el-input v-model="form.url" placeholder="https://example.com/webhook" />
        </el-form-item>
        <el-form-item label="签名密钥（可选）">
          <el-input v-model="form.secret" placeholder="用于 HMAC-SHA256 签名验证" />
          <el-text type="info" size="small">平台会以 <code>X-CodeSeer-Signature: sha256=...</code> 头发送签名</el-text>
        </el-form-item>
        <el-form-item label="订阅事件">
          <el-checkbox-group v-model="form.events">
            <el-checkbox v-for="ev in availableEvents" :key="ev.name" :value="ev.name">{{ ev.desc }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.enabled">启用</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeForm">取消</el-button>
        <el-button type="primary" :loading="saving" :disabled="!form.name.trim() || !form.url.trim()" @click="saveWebhook">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDeliveries" title="投递记录" width="720px">
      <el-table :data="deliveries" stripe size="small">
        <el-table-column prop="event" label="事件">
          <template #default="{ row }">
            <code>{{ row.event }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="response_status" label="响应" width="80" />
        <el-table-column label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">{{ row.success ? '成功' : '失败' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间">
          <template #default="{ row }">
            <el-text type="info" size="small">{{ formatDateTime(row.created_at) }}</el-text>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { webhooksApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const webhooks = ref<any[]>([])
const deliveries = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const showDeliveries = ref(false)
const editing = ref<any>(null)
const selectedWh = ref<any>(null)
const lastDeliveryMap = ref<Record<string, string>>({})

const form = ref({ name: '', url: '', secret: '', events: [] as string[], enabled: true })

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
  form.value = { name: wh.name, url: wh.url, secret: wh.secret || '', events: parseEvents(wh.events), enabled: wh.enabled }
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
    ElMessage.success('保存成功')
    fetchData()
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

const testWebhook = async (wh: any) => {
  try {
    await webhooksApi.test(wh.id)
    ElMessage.success('测试事件已发送，请查看投递记录')
    setTimeout(() => viewDeliveries(wh), 500)
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '发送失败') }
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
  try {
    await ElMessageBox.confirm(`删除 Webhook「${wh.name}」？`, '提示', { type: 'warning' })
    await webhooksApi.delete(wh.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await webhooksApi.list()
    webhooks.value = res.data
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
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; }
.page-title { font-size:20px; font-weight:700; color:#1f2329; margin:0; }
.page-subtitle { font-size:13px; color:#969ba4; margin:4px 0 0 0; }
</style>
