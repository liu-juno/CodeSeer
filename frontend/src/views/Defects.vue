<template>
  <div class="defects-page">
    <div class="page-header"></div>

    <div class="toolbar mb-16">
      <div class="toolbar-filters">
        <el-select v-model="filter.status" placeholder="全部状态" style="width:120px;" clearable @change="fetchData">
          <el-option value="new" label="新建" />
          <el-option value="confirmed" label="待确认" />
          <el-option value="fixing" label="修复中" />
          <el-option value="verifying" label="待验证" />
          <el-option value="closed" label="已关闭" />
        </el-select>
        <el-select v-model="filter.severity" placeholder="全部严重" style="width:110px;" clearable @change="fetchData">
          <el-option value="fatal" label="致命" />
          <el-option value="critical" label="严重" />
          <el-option value="major" label="一般" />
          <el-option value="minor" label="轻微" />
        </el-select>
        <el-select v-model="filter.priority" placeholder="全部优先级" style="width:110px;" clearable @change="fetchData">
          <el-option value="p0" label="P0" />
          <el-option value="p1" label="P1" />
          <el-option value="p2" label="P2" />
          <el-option value="p3" label="P3" />
        </el-select>
        <el-input v-model="filter.assignee" placeholder="负责人" style="width:100px;" clearable @change="fetchData" />
        <el-input v-model="filter.creator_id" placeholder="创建人" style="width:100px;" clearable @change="fetchData" />
        <el-select v-model="filter.module_id" placeholder="全部模块" style="width:140px;" clearable @change="fetchData">
          <el-option v-for="m in flatModules" :key="m.id" :label="m.path + m.name" :value="m.id" />
        </el-select>
      </div>
      <div class="toolbar-actions">
        <template v-if="viewMode === 'kanban'">
          <span class="lane-label">泳道：</span>
          <el-radio-group v-model="laneBy" size="small">
            <el-radio-button value="status">状态</el-radio-button>
            <el-radio-button value="priority">优先级</el-radio-button>
            <el-radio-button value="severity">严重程度</el-radio-button>
          </el-radio-group>
          <el-divider direction="vertical" />
        </template>
        <el-button type="primary" @click="$router.push('/defects/new')">
          <el-icon><Plus /></el-icon> 新建缺陷
        </el-button>
        <el-radio-group v-model="viewMode">
          <el-radio-button value="kanban">看板</el-radio-button>
          <el-radio-button value="list">列表</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 看板视图 -->
    <div v-if="viewMode === 'kanban'" class="kanban-board">
      <div class="kanban-lanes">
        <div v-for="lane in laneItems" :key="lane.key" class="kanban-lane">
          <div class="lane-title">{{ lane.label }} <span class="lane-count">{{ lane.items.length }}</span></div>
          <div class="lane-cards">
            <div v-for="d in lane.items" :key="d.id" class="defect-card" @click="$router.push(`/defect/${d.id}`)">
              <div class="defect-card-title">{{ d.title }}</div>
              <div class="defect-card-meta">
                <el-tag size="small" :type="severityType(d.severity)">{{ severityLabel(d.severity) }}</el-tag>
                <el-tag size="small">{{ d.priority.toUpperCase() }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 列表视图 -->
    <el-card v-else shadow="never">
      <el-table :data="defects" stripe v-loading="loading" @row-click="row => $router.push(`/defect/${row.id}`)">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="severityType(row.severity)">{{ severityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <span :class="'priority-' + row.priority">{{ row.priority.toUpperCase() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="assignees" label="负责人" width="120">
          <template #default="{ row }">
            <span>{{ formatAssignees(row.assignees) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="creator_id" label="创建人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { defectsApi, modulesApi } from '@/api'
import { useProjectStore } from '@/stores/project'
import { Plus } from '@element-plus/icons-vue'

const projectStore = useProjectStore()

const modules = ref<any[]>([])
const defects = ref<any[]>([])
const loading = ref(false)
const viewMode = ref('kanban')
const laneBy = ref('status')
const filter = ref({
  status: null,
  severity: null,
  priority: null,
  assignee: null,
  creator_id: null,
  module_id: null,
})

const flatModules = computed(() => {
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

const laneConfig = computed(() => {
  if (laneBy.value === 'status') {
    return [
      { key: 'new', label: '新建' },
      { key: 'confirmed', label: '待确认' },
      { key: 'fixing', label: '修复中' },
      { key: 'verifying', label: '待验证' },
      { key: 'closed', label: '已关闭' },
    ]
  }
  if (laneBy.value === 'priority') {
    return [
      { key: 'p0', label: 'P0' },
      { key: 'p1', label: 'P1' },
      { key: 'p2', label: 'P2' },
      { key: 'p3', label: 'P3' },
    ]
  }
  return [
    { key: 'fatal', label: '致命' },
    { key: 'critical', label: '严重' },
    { key: 'major', label: '一般' },
    { key: 'minor', label: '轻微' },
  ]
})

const laneItems = computed(() => {
  return laneConfig.value.map(l => ({
    ...l,
    items: defects.value.filter(d => (d[laneBy.value] === l.key))
  }))
})

const statusLabel = (s: string) => ({ new: '新建', confirmed: '待确认', fixing: '修复中', verifying: '待验证', closed: '已关闭' }[s] || s)
const severityLabel = (s: string) => ({ fatal: '致命', critical: '严重', major: '一般', minor: '轻微' }[s] || s)
const severityType = (s: string) => ({ fatal: 'danger', critical: 'danger', major: 'warning', minor: 'info' }[s] || 'info')
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '-'
const formatAssignees = (arr: string[]) => arr?.length ? arr.join(', ') : '-'

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (projectStore.currentProjectId) params.project_id = projectStore.currentProjectId
    if (projectStore.currentIterationId) params.iteration_id = projectStore.currentIterationId
    if (filter.value.status) params.status = filter.value.status
    if (filter.value.severity) params.severity = filter.value.severity
    if (filter.value.priority) params.priority = filter.value.priority
    if (filter.value.assignee) params.assignee = filter.value.assignee
    if (filter.value.creator_id) params.creator_id = filter.value.creator_id
    if (filter.value.module_id) params.module_id = filter.value.module_id
    const res = await defectsApi.list(params)
    defects.value = res.data
  } finally {
    loading.value = false
  }
}

watch(
  [() => projectStore.currentProjectId, () => projectStore.currentIterationId],
  () => fetchData()
)

onMounted(async () => {
  modules.value = (await modulesApi.list()).data
  fetchData()
})
</script>

<style scoped>
.toolbar { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.toolbar-filters { display:flex; align-items:center; gap:8px; flex-shrink:1; min-width:0; overflow:hidden; }
.toolbar-actions { display:flex; align-items:center; gap:8px; flex-shrink:0; }
.lane-label { font-size:13px; color:#6b7280; white-space:nowrap; }
.kanban-board { overflow-x:auto; }
.kanban-lanes { display:flex; gap:16px; min-width:max-content; }
.kanban-lane { width:280px; }
.lane-title {
  font-size:13px; font-weight:600; color:#6b7280;
  padding:8px 12px; background:#f9fafb; border-radius:6px 6px 0 0;
  display:flex; align-items:center; gap:8px;
}
.lane-count {
  background:#e5e7eb; border-radius:10px; padding:0 6px;
  font-size:11px; color:#6b7280;
}
.lane-cards { display:flex; flex-direction:column; gap:8px; padding:12px; background:#f3f4f6; border-radius:0 0 8px 8px; min-height:200px; }
.defect-card {
  background:#fff; border:1px solid #e5e7eb; border-radius:8px; padding:12px;
  cursor:pointer; transition:box-shadow .15s;
}
.defect-card:hover { box-shadow:0 2px 8px rgba(0,0,0,.1); }
.defect-card-title { font-size:13px; font-weight:500; color:#111827; margin-bottom:8px; }
.defect-card-meta { display:flex; gap:6px; }
.priority-p0 { color:#dc2626; font-weight:700; }
.priority-p1 { color:#ea580c; font-weight:600; }
.priority-p2 { color:#ca8a04; }
.priority-p3 { color:#6b7280; }
</style>