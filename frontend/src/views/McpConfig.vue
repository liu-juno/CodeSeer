<template>
  <div class="mcp-config-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">MCP 配置</h1>
        <p class="page-subtitle">配置 Claude Code MCP 连接，让开发者通过 AI 接入平台</p>
      </div>
    </div>

    <!-- Connection info card -->
    <div class="card ai-card mb-16">
      <div class="ai-card-header">
        <div class="ai-card-icon">⬡</div>
        <div>
          <div class="ai-card-title">MCP 服务端点</div>
          <div class="ai-card-subtitle">将以下配置添加到开发者的 Claude Code 配置文件中</div>
        </div>
        <div class="connection-status">
          <span class="status-dot active"></span>
          <span class="status-text">服务运行中</span>
        </div>
      </div>
      <div class="code-block">
        <div class="code-header">
          <span>~/.claude/claude.json</span>
          <button class="btn btn-sm btn-ghost" @click="copyConfig">
            {{ copied ? '✓ 已复制' : '复制' }}
          </button>
        </div>
        <pre class="code-content">{{ mcpConfig }}</pre>
      </div>
    </div>

    <!-- Endpoints overview -->
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">
      <div class="card">
        <div class="card-title">MCP Tools</div>
        <div class="endpoint-list">
          <div v-for="tool in mcpTools" :key="tool.name" class="endpoint-item">
            <div class="endpoint-badge">tool</div>
            <div class="endpoint-info">
              <div class="endpoint-name">{{ tool.name }}</div>
              <div class="endpoint-desc text-muted text-small">{{ tool.desc }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">开发者接入流程</div>
        <div class="flow-steps">
          <div v-for="(step, i) in devSteps" :key="i" class="flow-step">
            <div class="flow-step-num">{{ i + 1 }}</div>
            <div class="flow-step-content">
              <div class="flow-step-title">{{ step.title }}</div>
              <div class="flow-step-desc text-muted text-small">{{ step.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- API endpoints -->
    <div class="card">
      <div class="card-title">REST API 端点</div>
      <table class="table">
        <thead>
          <tr>
            <th>方法</th>
            <th>路径</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ep in apiEndpoints" :key="ep.path">
            <td><span :class="['method-badge', ep.method.toLowerCase()]">{{ ep.method }}</span></td>
            <td><code class="endpoint-code">{{ ep.path }}</code></td>
            <td class="text-muted text-medium">{{ ep.desc }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const copied = ref(false)

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
  { method: 'GET',  path: '/api/mcp/requirements',        desc: '获取进行中的需求' },
  { method: 'GET',  path: '/api/mcp/requirements/:id',    desc: '获取需求详情和任务' },
  { method: 'POST', path: '/api/mcp/sync-tasks',          desc: '同步任务列表' },
  { method: 'POST', path: '/api/mcp/update-task',         desc: '更新任务状态' },
  { method: 'POST', path: '/api/mcp/submit-test-result',  desc: '提交测试结果' },
  { method: 'POST', path: '/api/requirements/:id/transition', desc: '需求状态流转' },
]
</script>

<style scoped>
.ai-card {
  background: linear-gradient(135deg, #0f0f17 0%, #1a1a2e 100%);
  border-color: rgba(99,102,241,0.3);
  color: #e5e7eb;
}
.ai-card-header {
  display: flex; align-items: flex-start; gap: 14px; margin-bottom: 20px;
}
.ai-card-icon {
  font-size: 28px; color: #8b5cf6; flex-shrink: 0; line-height: 1;
}
.ai-card-title { font-size: 15px; font-weight: 600; color: #f9fafb; }
.ai-card-subtitle { font-size: 13px; color: #9ca3af; margin-top: 3px; }
.connection-status {
  margin-left: auto; display: flex; align-items: center; gap: 6px;
}
.status-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #6b7280;
}
.status-dot.active { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.5); }
.status-text { font-size: 12px; color: #9ca3af; }
.code-block { border-radius: 8px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); }
.code-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 14px; background: rgba(255,255,255,0.05);
  font-size: 12px; color: #9ca3af; font-family: monospace;
}
.code-content {
  margin: 0; padding: 16px; background: rgba(0,0,0,0.3);
  font-size: 13px; line-height: 1.6; color: #a5b4fc; font-family: monospace;
  overflow-x: auto; white-space: pre;
}

.endpoint-list { display: flex; flex-direction: column; gap: 10px; }
.endpoint-item { display: flex; align-items: flex-start; gap: 10px; }
.endpoint-badge {
  font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px;
  background: rgba(139,92,246,0.1); color: #8b5cf6; border: 1px solid rgba(139,92,246,0.2);
  flex-shrink: 0; margin-top: 1px; letter-spacing: 0.04em;
}
.endpoint-name { font-size: 13px; font-weight: 600; color: #111827; font-family: monospace; }
.endpoint-desc { margin-top: 2px; }

.flow-steps { display: flex; flex-direction: column; gap: 14px; }
.flow-step { display: flex; gap: 12px; }
.flow-step-num {
  width: 24px; height: 24px; border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.flow-step-title { font-size: 13.5px; font-weight: 600; color: #111827; }
.flow-step-desc { margin-top: 2px; }

.method-badge {
  font-size: 11px; font-weight: 700; padding: 2px 7px;
  border-radius: 4px; letter-spacing: 0.04em;
}
.method-badge.get  { background: #d1fae5; color: #065f46; }
.method-badge.post { background: #dbeafe; color: #1e40af; }
.method-badge.put  { background: #fef9c3; color: #a16207; }
.method-badge.delete { background: #fee2e2; color: #991b1b; }

.endpoint-code {
  font-family: monospace; font-size: 13px; color: #4f46e5;
  background: #f5f3ff; padding: 2px 6px; border-radius: 4px;
}
</style>
