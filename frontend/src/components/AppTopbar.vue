<template>
  <header class="app-topbar">
    <div class="topbar-left">
      <el-dropdown
        v-if="showIterationSelector"
        trigger="click"
        @command="onIterationSelect"
      >
        <div class="iteration-selector">
          <el-icon><Calendar /></el-icon>
          <span class="iteration-label">{{ currentIterationLabel }}</span>
          <el-icon class="arrow-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null">全部</el-dropdown-item>
            <el-dropdown-item
              v-for="it in iterations"
              :key="it.id"
              :command="it"
            >
              {{ it.name }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <div v-else class="iteration-selector disabled">
        <el-icon><Calendar /></el-icon>
        <span class="iteration-label">—</span>
      </div>

      <span v-if="breadcrumb" class="topbar-breadcrumb">{{ breadcrumb }}</span>
    </div>

    <div class="topbar-right">
      <el-icon class="topbar-action" @click="toggle">
        <Sunny v-if="isDark" />
        <Moon v-else />
      </el-icon>

      <el-dropdown trigger="click">
        <div class="user-avatar">{{ userInitial }}</div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="openTokenDialog">MCP Token 管理</el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>

  <!-- Token 管理对话框 -->
  <el-dialog v-model="tokenDialogVisible" title="MCP Token 管理" width="480px" @open="fetchTokens">
    <div style="margin-bottom:16px; display:flex; justify-content:flex-end;">
      <el-button size="small" type="primary" @click="showCreate = true">+ 申请新 Token</el-button>
    </div>
    <el-empty v-if="tokens.length === 0" description="暂无 Token，点击「申请新 Token」创建" />
    <div v-for="t in tokens" :key="t.id" class="token-item">
      <div class="token-info">
        <span class="token-name">{{ t.name }}</span>
        <code class="token-prefix">{{ t.prefix }}…</code>
        <el-text type="info" size="small">{{ t.expires_at ? '过期: ' + t.expires_at.slice(0,10) : '永不过期' }}</el-text>
      </div>
      <el-button size="small" text type="danger" @click="handleRevoke(t.id)">撤销</el-button>
    </div>
  </el-dialog>

  <!-- 申请新 Token 对话框 -->
  <el-dialog v-model="showCreate" title="申请新 Access Token" width="400px" :append-to-body="true">
    <div v-if="newlyCreatedToken">
      <el-alert type="warning" :closable="false" style="margin-bottom:12px;">Token 已创建，请立即复制保存，此后不再显示</el-alert>
      <code style="display:block; font-size:13px; word-break:break-all; background:#f9fafb; border:1px solid #e5e7eb; border-radius:6px; padding:10px; color:#374151;">{{ newlyCreatedToken }}</code>
      <el-button size="small" style="margin-top:8px;" @click="copyNewToken">{{ tokenCopied ? '✓ 已复制' : '复制' }}</el-button>
    </div>
    <el-input v-else v-model="newTokenName" placeholder="Token 名称，如 CI / 本地开发" />
    <template #footer>
      <el-button @click="closeCreate">关闭</el-button>
      <el-button v-if="!newlyCreatedToken" type="primary" :disabled="!newTokenName" @click="handleCreate">创建</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { useTheme } from '@/composables/useTheme'
import { useTokenManager } from '@/composables/useTokenManager'
import { iterationsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, ArrowDown, Sunny, Moon } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const projectStore = useProjectStore()
const { isDark, toggle } = useTheme()

const iterations = ref<any[]>([])

// Token management
const tokenDialogVisible = ref(false)
const showCreate = ref(false)
const newTokenName = ref('')
const newlyCreatedToken = ref<string | null>(null)
const tokenCopied = ref(false)

const currentUserId = computed(() => auth.user?.id ?? '')
const { tokens, fetchTokens, createToken, revokeToken } = useTokenManager(currentUserId.value)

function openTokenDialog() {
  tokenDialogVisible.value = true
}

async function handleCreate() {
  const result = await createToken({ name: newTokenName.value, user_id: currentUserId.value })
  newlyCreatedToken.value = result.token
  newTokenName.value = ''
}

async function handleRevoke(id: string) {
  try {
    await ElMessageBox.confirm('确认撤销此 Token？', '提示', { type: 'warning' })
    await revokeToken(id)
    ElMessage.success('撤销成功')
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

async function copyNewToken() {
  if (newlyCreatedToken.value) {
    await navigator.clipboard.writeText(newlyCreatedToken.value)
    tokenCopied.value = true
    setTimeout(() => { tokenCopied.value = false }, 2000)
  }
}

function closeCreate() {
  showCreate.value = false
  newlyCreatedToken.value = null
}

const NO_ITERATION_ROUTES = [
  '/documents', '/standup', '/users', '/settings',
  '/mcp-config', '/modules', '/webhooks',
]
const showIterationSelector = computed(() =>
  !NO_ITERATION_ROUTES.some(r => route.path === r || route.path.startsWith(r + '/'))
)

const currentIterationLabel = computed(
  () => projectStore.currentIteration?.name ?? '选择迭代'
)

const BREADCRUMB_MAP: Record<string, string> = {
  '/dashboard':     '概览',
  '/requirements':  '需求管理',
  '/defects':       '缺陷管理',
  '/iterations':    '迭代管理',
  '/documents':     '文档管理',
  '/standup':       '站会',
  '/users':         '成员管理',
  '/settings':      '设置',
  '/mcp-config':    'MCP 配置',
  '/modules':       '模块',
  '/webhooks':      'Webhooks',
  '/projects':      '项目管理',
}

const breadcrumb = computed(() => {
  for (const [prefix, label] of Object.entries(BREADCRUMB_MAP)) {
    if (route.path === prefix || route.path.startsWith(prefix + '/')) return label
  }
  return ''
})

const userInitial = computed(
  () => (auth.user?.name || '用户').charAt(0).toUpperCase()
)

async function fetchIterations() {
  if (!projectStore.currentProjectId) return
  try {
    const res = await iterationsApi.byProject(projectStore.currentProjectId)
    iterations.value = res.data
  } catch { /* silently ignore */ }
}

function onIterationSelect(it: any | null) {
  projectStore.setCurrentIteration(it)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

watch(() => projectStore.currentProjectId, fetchIterations)
onMounted(fetchIterations)
</script>

<style scoped>
.app-topbar {
  height: var(--topbar-height);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 clamp(12px, 1.5vw, 24px);
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.iteration-selector {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-btn);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-primary);
  white-space: nowrap;
  transition: background 0.15s;
  user-select: none;
}

.iteration-selector:not(.disabled):hover {
  background: var(--bg-hover);
}

.iteration-selector.disabled {
  color: var(--text-muted);
  cursor: default;
}

.iteration-label {
  max-width: 16ch;
  overflow: hidden;
  text-overflow: ellipsis;
}

.arrow-icon {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.topbar-breadcrumb {
  font-size: 0.875rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.topbar-action {
  font-size: 1.125rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.375rem;
  border-radius: var(--radius-btn);
  transition: background 0.15s, color 0.15s;
}

.topbar-action:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.user-avatar {
  width: 1.75rem;
  height: 1.75rem;
  background: var(--color-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  user-select: none;
}

.token-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  margin-bottom: 8px;
}

.token-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.token-name {
  font-size: 13.5px;
  font-weight: 600;
  color: #111827;
}

.token-prefix {
  font-size: 12px;
  color: #6366f1;
  background: #f5f3ff;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
