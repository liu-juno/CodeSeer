<template>
  <div class="defect-detail-page">
    <div class="page-header"></div>

    <div v-if="defect" class="defect-content">
      <el-card shadow="never" style="margin-bottom:16px;">
        <template #header>
          <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:16px;">
            <div>
              <h2 class="detail-title">{{ defect.title }}</h2>
              <div style="display:flex; gap:8px; margin-top:8px; flex-wrap:wrap;">
                <el-tag size="small">{{ statusLabel(defect.status) }}</el-tag>
                <el-tag size="small" :type="severityType(defect.severity)">{{ severityLabel(defect.severity) }}</el-tag>
                <el-tag size="small">{{ defect.priority.toUpperCase() }}</el-tag>
              </div>
            </div>
            <div style="display:flex; gap:8px; flex-shrink:0;">
              <el-select v-model="newStatus" style="width:120px;" @change="changeStatus">
                <el-option value="new" label="新建" />
                <el-option value="confirmed" label="待确认" />
                <el-option value="fixing" label="修复中" />
                <el-option value="verifying" label="待验证" />
                <el-option value="closed" label="已关闭" />
              </el-select>
              <el-button type="primary" @click="showEdit = true">编辑</el-button>
            </div>
          </div>
        </template>

        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="项目">{{ projectName }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ formatAssignees(defect.assignees) }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">{{ severityLabel(defect.severity) }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ defect.priority.toUpperCase() }}</el-descriptions-item>
          <el-descriptions-item label="关联需求">{{ defect.requirement_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关联模块">{{ defect.module_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关联迭代">{{ defect.iteration_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="标签">{{ defect.labels?.join(', ') || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建人">{{ defect.creator_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(defect.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="复现步骤" :span="2">{{ defect.steps_to_reproduce || '-' }}</el-descriptions-item>
          <el-descriptions-item label="环境" :span="2">{{ defect.environment || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="defect.description" style="margin-top:16px;">
          <div class="field-label">描述</div>
          <MarkdownRenderer :content="defect.description" />
        </div>
      </el-card>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="评论" name="comments">
          <el-card shadow="never">
            <div v-if="comments.length === 0" style="color:#9ca3af; text-align:center; padding:20px;">暂无评论</div>
            <div v-else class="comment-list">
              <div v-for="c in comments" :key="c.id" class="comment-item">
                <div class="comment-header">
                  <span class="comment-user">{{ c.user_id || '未知用户' }}</span>
                  <span class="comment-time">{{ formatDate(c.created_at) }}</span>
                </div>
                <div class="comment-content">{{ c.content }}</div>
              </div>
            </div>
            <div style="margin-top:16px; display:flex; gap:8px;">
              <el-input v-model="newComment" type="textarea" :rows="2" placeholder="输入评论..." />
              <el-button type="primary" @click="submitComment" :disabled="!newComment.trim()">发送</el-button>
            </div>
          </el-card>
        </el-tab-pane>
        <el-tab-pane label="变更日志" name="logs">
          <el-card shadow="never">
            <el-timeline v-if="logs.length">
              <el-timeline-item v-for="log in logs" :key="log.id" :timestamp="formatDate(log.created_at)" placement="top">
                <div class="log-action">{{ logActionLabel(log.action) }}</div>
                <div v-if="log.old_value || log.new_value" class="log-change">
                  <span v-if="log.old_value">{{ log.old_value }} → </span>{{ log.new_value }}
                </div>
                <div v-if="log.user_id" class="log-user">操作人: {{ log.user_id }}</div>
              </el-timeline-item>
            </el-timeline>
            <div v-else style="color:#9ca3af; text-align:center; padding:20px;">暂无变更记录</div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="showEdit" title="编辑缺陷" width="640px">
      <el-form :model="editForm" label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="描述">
          <VditorEditor v-model="editForm.description" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="严重程度">
              <el-select v-model="editForm.severity" style="width:100%;">
                <el-option value="fatal" label="致命" />
                <el-option value="critical" label="严重" />
                <el-option value="major" label="一般" />
                <el-option value="minor" label="轻微" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="editForm.priority" style="width:100%;">
                <el-option value="p0" label="P0" />
                <el-option value="p1" label="P1" />
                <el-option value="p2" label="P2" />
                <el-option value="p3" label="P3" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="负责人（多人用逗号分隔）">
          <el-input v-model="assigneesInput" placeholder="用户ID，多人用逗号分隔" />
        </el-form-item>
        <el-form-item label="标签（多个用逗号分隔）">
          <el-input v-model="labelsInput" placeholder="标签，多个用逗号分隔" />
        </el-form-item>
        <el-form-item label="复现步骤">
          <el-input v-model="editForm.steps_to_reproduce" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="环境">
          <el-input v-model="editForm.environment" placeholder="如: Chrome 120 / Windows 11" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { defectsApi, projectsApi } from '@/api'
import { ElMessage } from 'element-plus'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import VditorEditor from '@/components/VditorEditor.vue'

const route = useRoute()
const router = useRouter()
const defect = ref<any>(null)
const projects = ref<any[]>([])
const comments = ref<any[]>([])
const logs = ref<any[]>([])
const loading = ref(false)
const activeTab = ref('comments')
const newComment = ref('')
const showEdit = ref(false)
const saving = ref(false)
const newStatus = ref('')
const editForm = ref<any>({})
const assigneesInput = ref('')
const labelsInput = ref('')

const statusLabel = (s: string) => ({ new: '新建', confirmed: '待确认', fixing: '修复中', verifying: '待验证', closed: '已关闭' }[s] || s)
const severityLabel = (s: string) => ({ fatal: '致命', critical: '严重', major: '一般', minor: '轻微' }[s] || s)
const severityType = (s: string) => ({ fatal: 'danger', critical: 'danger', major: 'warning', minor: 'info' }[s] || 'info')
const formatDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN') : '-'
const formatAssignees = (arr: any) => Array.isArray(arr) ? arr.join(', ') : arr || '-'
const logActionLabel = (a: string) => ({ created: '创建缺陷', status_changed: '状态变更', commented: '添加评论', updated: '更新' }[a] || a)

const projectName = computed(() => {
  const p = projects.value.find(x => x.id === defect.value?.project_id)
  return p?.name || defect.value?.project_id || '-'
})

const fetchData = async () => {
  loading.value = true
  try {
    const id = route.params.id as string
    const [defectRes, commentsRes, logsRes, projectsRes] = await Promise.all([
      defectsApi.get(id),
      defectsApi.listComments(id),
      defectsApi.listLogs(id),
      projectsApi.list(),
    ])
    defect.value = defectRes.data
    newStatus.value = defectRes.data.status
    comments.value = commentsRes.data
    logs.value = logsRes.data
    projects.value = projectsRes.data.items ?? projectsRes.data
    editForm.value = { ...defectRes.data }
    assigneesInput.value = (defectRes.data.assignees || []).join(', ')
    labelsInput.value = (defectRes.data.labels || []).join(', ')
  } finally {
    loading.value = false
  }
}

const changeStatus = async () => {
  try {
    await defectsApi.update(route.params.id as string, { status: newStatus.value })
    ElMessage.success('状态已更新')
    fetchData()
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const submitComment = async () => {
  try {
    await defectsApi.createComment(route.params.id as string, { content: newComment.value })
    newComment.value = ''
    comments.value = (await defectsApi.listComments(route.params.id as string)).data
    ElMessage.success('评论已发送')
  } catch (e) {
    ElMessage.error('发送失败')
  }
}

const saveEdit = async () => {
  saving.value = true
  try {
    const data: any = { ...editForm.value }
    data.assignees = assigneesInput.value.split(',').map(s => s.trim()).filter(Boolean)
    data.labels = labelsInput.value.split(',').map(s => s.trim()).filter(Boolean)
    await defectsApi.update(route.params.id as string, data)
    showEdit.value = false
    ElMessage.success('保存成功')
    fetchData()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.detail-title { font-size:20px; font-weight:700; color:#1f2329; margin:0; }
.field-label { font-size:12px; font-weight:600; color:#6b7280; margin-bottom:8px; }
.comment-list { display:flex; flex-direction:column; gap:16px; }
.comment-item { padding-bottom:16px; border-bottom:1px solid #f3f4f6; }
.comment-header { display:flex; gap:12px; align-items:center; margin-bottom:6px; }
.comment-user { font-weight:600; font-size:13px; color:#111827; }
.comment-time { font-size:12px; color:#9ca3af; }
.comment-content { font-size:14px; color:#374151; line-height:1.6; }
.log-action { font-weight:600; font-size:13px; color:#111827; }
.log-change { font-size:13px; color:#6b7280; margin-top:4px; }
.log-user { font-size:12px; color:#9ca3af; margin-top:4px; }
</style>