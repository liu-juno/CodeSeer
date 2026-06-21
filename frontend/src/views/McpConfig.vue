<template>
  <div class="mcp-config-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">MCP 配置</h1>
        <p class="page-subtitle">配置 Claude Code MCP 连接，让开发者通过 AI 接入平台</p>
      </div>
    </div>

    <el-card shadow="never" class="ai-card" style="margin-bottom:16px;">
      <template #header>
        <div style="display:flex; align-items:flex-start; gap:14px;">
          <div style="font-size:28px; color:#8b5cf6;">⬡</div>
          <div style="flex:1;">
            <div style="font-weight:600; color:#f9fafb;">MCP 服务端点</div>
            <div style="font-size:13px; color:#9ca3af; margin-top:3px;">将以下配置添加到开发者的 Claude Code 配置文件中</div>
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <span style="width:8px; height:8px; border-radius:50%; background:#22c55e; box-shadow:0 0 6px rgba(34,197,94,0.5);"></span>
            <span style="font-size:12px; color:#9ca3af;">服务运行中</span>
          </div>
        </div>
      </template>
      <div style="border-radius:8px; overflow:hidden; border:1px solid rgba(255,255,255,0.08);">
        <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 14px; background:rgba(255,255,255,0.05); font-size:12px; color:#9ca3af; font-family:monospace;">
          <span>~/.claude/claude.json</span>
          <el-button size="small" text @click="copyConfig">{{ copied ? '✓ 已复制' : '复制' }}</el-button>
        </div>
        <pre style="margin:0; padding:16px; background:rgba(0,0,0,0.3); font-size:13px; line-height:1.6; color:#a5b4fc; font-family:monospace; overflow-x:auto; white-space:pre;">{{ mcpConfig }}</pre>
      </div>
    </el-card>

    <el-row :gutter="16" style="margin-bottom:16px;">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div style="font-weight:600;">MCP Tools</div>
          </template>
          <div v-for="tool in mcpTools" :key="tool.name" style="display:flex; gap:10px; margin-bottom:10px;">
            <span style="font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px; background:rgba(139,92,246,0.1); color:#8b5cf6; border:1px solid rgba(139,92,246,0.2); flex-shrink:0; margin-top:1px; letter-spacing:0.04em;">tool</span>
            <div>
              <div style="font-size:13px; font-weight:600; color:#111827; font-family:monospace;">{{ tool.name }}</div>
              <div style="font-size:12px; color:#6b7280; margin-top:2px;">{{ tool.desc }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div style="font-weight:600;">开发者接入流程</div>
          </template>
          <div v-for="(step, i) in devSteps" :key="i" style="display:flex; gap:12px; margin-bottom:14px;">
            <div style="width:24px; height:24px; border-radius:50%; background:linear-gradient(135deg, #6366f1, #8b5cf6); color:white; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0;">{{ i + 1 }}</div>
            <div>
              <div style="font-size:13.5px; font-weight:600; color:#111827;">{{ step.title }}</div>
              <div style="font-size:12px; color:#6b7280; margin-top:2px;">{{ step.desc }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-bottom:16px;">
      <template #header>
        <div style="display:flex; align-items:center; justify-content:space-between;">
          <div style="font-weight:600;">Access Token 管理</div>
          <el-button size="small" @click="showCreateModal = true">+ 申请新 Token</el-button>
        </div>
      </template>
      <el-empty v-if="tokens.length === 0" description="暂无 Token，点击「申请新 Token」创建" />
      <div v-else v-for="t in tokens" :key="t.id" style="display:flex; align-items:center; justify-content:space-between; padding:10px 12px; border-radius:8px; border:1px solid #e5e7eb; margin-bottom:10px;">
        <div style="display:flex; align-items:center; gap:12px;">
          <span style="font-size:13.5px; font-weight:600; color:#111827;">{{ t.name }}</span>
          <code style="font-size:12px; color:#6366f1; background:#f5f3ff; padding:2px 6px; border-radius:4px;">{{ t.prefix }}…</code>
          <el-text type="info" size="small">{{ t.expires_at ? '过期: ' + t.expires_at.slice(0, 10) : '永不过期' }}</el-text>
        </div>
        <el-button size="small" text type="danger" @click="handleRevoke(t.id)">撤销</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div style="font-weight:600;">REST API 端点</div>
      </template>
      <el-table :data="apiEndpoints" stripe size="small">
        <el-table-column prop="method" label="方法" width="80">
          <template #default="{ row }">
            <el-tag :type="methodType(row.method)" size="small">{{ row.method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" min-width="300">
          <template #default="{ row }">
            <code style="font-family:monospace; font-size:13px; color:#4f46e5; background:#f5f3ff; padding:2px 6px; border-radius:4px;">{{ row.path }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="desc" label="说明" />
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateModal" title="申请新 Access Token" width="400px">
      <div v-if="newlyCreatedToken">
        <el-alert type="warning" :closable="false" style="margin-bottom:12px;">Token 已创建，请立即复制保存，此后不再显示</el-alert>
        <code style="display:block; font-size:13px; word-break:break-all; background:#f9fafb; border:1px solid #e5e7eb; border-radius:6px; padding:10px; color:#374151;">{{ newlyCreatedToken }}</code>
        <el-button size="small" style="margin-top:8px;" @click="copyNewToken">{{ tokenCopied ? '✓ 已复制' : '复制' }}</el-button>
      </div>
      <template v-else>
        <el-input v-model="newTokenName" placeholder="Token 名称，如 CI / 本地开发" />
      </template>
      <template #footer>
        <el-button @click="closeCreateModal">关闭</el-button>
        <el-button v-if="!newlyCreatedToken" type="primary" :disabled="!newTokenName" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useTokenManager } from '@/composables/useTokenManager'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const copied = ref(false)
const tokenCopied = ref(false)
const authStore = useAuthStore()
const currentUserId = computed(() => authStore.user?.id ?? '')
const { tokens, fetchTokens, createToken, revokeToken } = useTokenManager(currentUserId.value)
const showCreateModal = ref(false)
const newTokenName = ref('')
const newlyCreatedToken = ref<string | null>(null)

onMounted(fetchTokens)

const handleCreate = async () => {
  const result = await createToken({ name: newTokenName.value, user_id: currentUserId.value })
  newlyCreatedToken.value = result.token
  newTokenName.value = ''
}

const handleRevoke = async (id: string) => {
  try {
    await ElMessageBox.confirm('确认撤销此 Token？', '提示', { type: 'warning' })
    await revokeToken(id)
    ElMessage.success('撤销成功')
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

const copyNewToken = async () => {
  if (newlyCreatedToken.value) {
    await navigator.clipboard.writeText(newlyCreatedToken.value)
    tokenCopied.value = true
    setTimeout(() => { tokenCopied.value = false }, 2000)
  }
}

const closeCreateModal = () => {
  showCreateModal.value = false
  newlyCreatedToken.value = null
}

const mcpConfig = `{
  "mcpServers": {
    "codeseer": {
      "command": "node",
      "args": ["/path/to/CodeSeer/mcp-server/src/index.js"],
      "env": {
        "CODESEER_API_URL": "http://localhost:8000/api",
        "CODESEER_DEVELOPER_ID": "your-email@company.com"
      }
    }
  }
}`

const copyConfig = async () => {
  await navigator.clipboard.writeText(mcpConfig)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

const methodType = (m: string) => ({ GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger' }[m] || 'info')

const mcpTools = [
  { name: 'list_assigned_requirements', desc: '获取指派给当前开发的需求列表' },
  { name: 'get_requirement_detail', desc: '获取需求详情、任务、测试记录' },
  { name: 'sync_tasks', desc: '同步 Superpower 拆分的任务列表' },
  { name: 'update_task_status', desc: '更新任务状态和 TDD 进度' },
  { name: 'submit_test_result', desc: '提交单元测试结果' },
  { name: 'update_requirement_status', desc: '更新需求状态流转' },
]

const devSteps = [
  { title: '配置 MCP', desc: '将配置粘贴到 ~/.claude/claude.json，把路径和 ID 替换为实际值' },
  { title: '接受任务', desc: '在 Claude Code 中调用 list_assigned_requirements 获取需求' },
  { title: '同步任务', desc: 'AI 拆解子任务后，通过 sync_tasks 一次性同步到平台' },
  { title: '开发并更新进度', desc: '完成 TDD 每个步骤后调用 update_task_status 更新状态' },
  { title: '提交测试', desc: '运行测试套件后通过 submit_test_result 上报覆盖率和结果' },
  { title: '提交评审', desc: '调用 update_requirement_status 将需求推进至「待评审」' },
]

const apiEndpoints = [
  { method: 'GET', path: '/api/mcp/requirements', desc: '获取进行中的需求' },
  { method: 'GET', path: '/api/mcp/requirements/:id', desc: '获取需求详情和任务' },
  { method: 'POST', path: '/api/mcp/sync-tasks', desc: '同步任务列表' },
  { method: 'POST', path: '/api/mcp/update-task', desc: '更新任务状态' },
  { method: 'POST', path: '/api/mcp/submit-test-result', desc: '提交测试结果' },
  { method: 'POST', path: '/api/requirements/:id/transition', desc: '需求状态流转' },
]
</script>

<style scoped>
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; }
.page-title { font-size:20px; font-weight:700; color:#1f2329; margin:0; }
.page-subtitle { font-size:13px; color:#969ba4; margin:4px 0 0 0; }
.ai-card { background:linear-gradient(135deg, #0f0f17 0%, #1a1a2e 100%); border-color:rgba(99,102,241,0.3); }
</style>
