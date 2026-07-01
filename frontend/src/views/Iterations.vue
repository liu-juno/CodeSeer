<template>
  <div class="iterations-page">
    <div class="page-header">
      <div class="header-right">
        <el-input v-model="search" placeholder="搜索迭代..." style="width:200px;" clearable @input="onSearch" />
        <el-select v-model="statusFilter" placeholder="全部状态" style="width:120px" clearable @change="onFilterChange">
          <el-option value="planning" label="规划中" />
          <el-option value="development" label="开发中" />
          <el-option value="testing" label="测试中" />
          <el-option value="released" label="已发布" />
          <el-option value="archived" label="已关闭" />
        </el-select>
        <el-button type="primary" @click="showCreateModal = true">
          <el-icon><Plus /></el-icon> 创建迭代
        </el-button>
      </div>
    </div>

    <el-table :data="filteredIterations" stripe style="width:100%">
      <el-table-column type="selection" width="40" />
      <el-table-column prop="name" label="迭代名称" min-width="200">
        <template #default="{ row }">
          <el-link type="primary" underline="never" @click="$router.push(`/iteration/${row.id}`)">
            {{ row.name }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="130">
        <template #default="{ row }">
          <el-select
            :model-value="row.status"
            size="small"
            style="width:110px;"
            @change="(val: string) => changeStatus(row, val)"
          >
            <el-option value="planning" label="规划中" />
            <el-option value="development" label="开发中" />
            <el-option value="testing" label="测试中" />
            <el-option value="released" label="已发布" />
            <el-option value="archived" label="已关闭" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="planned_release_date" label="计划发布日期" width="140">
        <template #default="{ row }">
          <el-text class="text-muted">{{ row.planned_release_date ? formatDate(row.planned_release_date) : '—' }}</el-text>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="120">
        <template #default="{ row }">
          <el-text class="text-muted text-small">{{ formatDate(row.created_at) }}</el-text>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" align="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="$router.push(`/iteration/${row.id}`)">查看</el-button>
          <el-button size="small" text type="danger" @click="deleteIteration(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      background
      layout="total, sizes, prev, pager, next, jumper"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @size-change="onSizeChange"
      @current-change="onPageChange"
      style="margin-top: 20px; justify-content: flex-end;"
    />

    <el-dialog v-model="showCreateModal" title="创建迭代" width="520px">
      <el-form :model="newIteration" label-position="top">
        <el-form-item label="迭代名称" required>
          <el-input v-model="newIteration.name" placeholder="如：v1.0.0 / Sprint-1" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newIteration.description" type="textarea" placeholder="本次迭代目标..." />
        </el-form-item>
        <el-form-item label="计划发布日期">
          <el-date-picker v-model="newIteration.planned_release_date" type="date" placeholder="选择日期" style="width:100%" value-format="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateModal = false">取消</el-button>
        <el-button type="primary" :disabled="!newIteration.name.trim()" @click="createIteration">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { iterationsApi } from '@/api'
import { usePagination } from '@/composables/usePagination'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const projectStore = useProjectStore()

const { items: iterations, total, page, pageSize, loading, fetchPage, onPageChange, onSizeChange } = usePagination(
  async (p, ps) => {
    if (!projectStore.currentProjectId) return { items: [], total: 0 }
    const all = (await iterationsApi.byProject(projectStore.currentProjectId)).data as any[]
    const start = (p - 1) * ps
    return { items: all.slice(start, start + ps), total: all.length }
  }
)

const showCreateModal = ref(false)
const search = ref('')
const statusFilter = ref('')

const newIteration = ref({ name: '', description: '', project_id: '', planned_release_date: '' })

const onSearch = () => fetchPage(1)
const onFilterChange = () => fetchPage(1)

const filteredIterations = computed(() => {
  let list = iterations.value
  if (search.value.trim()) {
    const q = search.value.trim().toLowerCase()
    list = list.filter((i: any) => i.name.toLowerCase().includes(q))
  }
  if (statusFilter.value) {
    list = list.filter((i: any) => i.status === statusFilter.value)
  }
  return list
})

const statusType = (s: string) => ({
  planning: 'info', development: 'primary', testing: 'warning',
  released: 'success', archived: 'info'
}[s] || 'info')

const statusText = (status: string) => ({
  planning: '规划中', development: '开发中', testing: '测试中',
  released: '已发布', archived: '已关闭',
}[status] || status)

const formatDate = (date: string) => new Date(date).toLocaleDateString('zh-CN')

watch(() => projectStore.currentProjectId, () => fetchPage(1))

const createIteration = async () => {
  try {
    await iterationsApi.create({
      ...newIteration.value,
      project_id: projectStore.currentProjectId,
    })
    showCreateModal.value = false
    newIteration.value = { name: '', description: '', project_id: '', planned_release_date: '' }
    ElMessage.success('创建成功')
    fetchPage(page.value)
  } catch (e) {
    console.error(e)
  }
}

const changeStatus = async (row: any, newStatus: string) => {
  try {
    await iterationsApi.update(row.id, { status: newStatus })
    row.status = newStatus
    ElMessage.success(`已更新为「${statusText(newStatus)}」`)
  } catch (e) { console.error(e) }
}

const deleteIteration = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除此迭代？', '提示', { type: 'warning' })
    await iterationsApi.delete(id)
    ElMessage.success('删除成功')
    fetchPage(page.value)
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

onMounted(() => fetchPage(1))
</script>

<style scoped>
.iterations-page { width: 100%; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.header-left, .header-right { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 20px; font-weight: 700; color: #1f2329; margin: 0; }
</style>
