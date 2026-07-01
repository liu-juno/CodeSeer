<template>
  <div class="project-settings-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="项目信息" name="info">
        <div class="section-header">
          <h3>基本信息</h3>
          <el-button type="primary" :loading="saving" @click="saveProjectInfo">保存</el-button>
        </div>
        <el-form :model="projectForm" label-position="top" style="max-width: 480px;">
          <el-form-item label="项目名称">
            <el-input v-model="projectForm.name" />
          </el-form-item>
          <el-form-item label="项目标识符">
            <el-input v-model="projectForm.identifier" />
          </el-form-item>
          <el-form-item label="项目描述">
            <el-input v-model="projectForm.description" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="projectForm.status">
              <el-option label="进行中" value="active" />
              <el-option label="已完成" value="completed" />
              <el-option label="已归档" value="archived" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane v-if="isProjectAdmin" label="成员管理" name="members">
        <div class="section-header">
          <h3>项目成员</h3>
          <el-button type="primary" @click="showAddDialog = true">添加成员</el-button>
        </div>

        <el-table :data="members" stripe>
          <el-table-column prop="user_name" label="姓名" />
          <el-table-column prop="user_email" label="邮箱" />
          <el-table-column prop="role" label="角色">
            <template #default="{ row }">
              <el-select v-model="row.role" @change="updateRole(row)">
                <el-option label="管理员" value="admin" />
                <el-option label="开发" value="dev" />
                <el-option label="测试" value="test" />
                <el-option label="产品" value="product" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态">
            <template #default="{ row }">
              <el-tag :type="row.status === 'approved' ? 'success' : 'warning'">
                {{ row.status === 'approved' ? '已加入' : '待审核' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="{ row }">
              <template v-if="row.status === 'pending'">
                <el-button size="small" type="success" @click="approve(row)">批准</el-button>
                <el-button size="small" type="danger" @click="reject(row)">拒绝</el-button>
              </template>
              <el-button v-else size="small" type="danger" @click="remove(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showAddDialog" title="添加成员" width="400px">
      <el-form :model="addForm">
        <el-form-item label="用户">
          <el-select v-model="addForm.userId" filterable placeholder="选择用户">
            <el-option v-for="user in users" :key="user.id" :label="`${user.name} (${user.email})`" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="addForm.role">
            <el-option label="管理员" value="admin" />
            <el-option label="开发" value="dev" />
            <el-option label="测试" value="test" />
            <el-option label="产品" value="product" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addMember">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi, usersApi } from '@/api'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const projectStore = useProjectStore()
const authStore = useAuthStore()
const projectId = route.params.id as string

const activeTab = ref((route.query.tab as string) || 'info')

watch(() => route.query.tab, (tab) => {
  activeTab.value = (tab as string) || 'info'
})
const members = ref<any[]>([])
const showAddDialog = ref(false)
const addForm = ref({ userId: '', role: 'dev' })
const users = ref<any[]>([])
const saving = ref(false)

// 只有全局管理员或项目管理员可以管理成员
const isProjectAdmin = computed(() => {
  if (authStore.user?.role === 'admin') return true
  const me = members.value.find(m => m.user_id === authStore.user?.id)
  return me?.role === 'admin'
})

const projectForm = ref({
  name: projectStore.currentProject?.name || '',
  identifier: projectStore.currentProject?.identifier || '',
  description: projectStore.currentProject?.description || '',
  status: projectStore.currentProject?.status || 'active',
})

watch(() => projectStore.currentProject, (p) => {
  if (p) {
    projectForm.value = {
      name: p.name || '',
      identifier: p.identifier || '',
      description: p.description || '',
      status: p.status || 'active',
    }
  }
}, { immediate: true })

onMounted(() => {
  loadMembers()
  loadUsers()
})

async function loadMembers() {
  try {
    const res = await projectsApi.listMembers(projectId)
    members.value = res.data
  } catch (e) {
    console.error('Failed to load members', e)
  }
}

async function loadUsers() {
  const res = await usersApi.list()
  users.value = res.data?.items || res.data || []
}

async function saveProjectInfo() {
  saving.value = true
  try {
    await projectsApi.update(projectId, {
      name: projectForm.value.name,
      identifier: projectForm.value.identifier,
      description: projectForm.value.description,
      status: projectForm.value.status,
    })
    ElMessage.success('保存成功')
    await projectStore.fetchMyProjects()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function addMember() {
  if (!addForm.value.userId) {
    ElMessage.error('请选择用户')
    return
  }
  try {
    await projectsApi.addMember(projectId, { user_id: addForm.value.userId, role: addForm.value.role })
    ElMessage.success('添加成功')
    showAddDialog.value = false
    addForm.value = { userId: '', role: 'dev' }
    loadMembers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  }
}

async function updateRole(row: any) {
  try {
    await projectsApi.updateMember(projectId, row.user_id, { role: row.role })
    ElMessage.success('更新成功')
  } catch (e: any) {
    ElMessage.error('更新失败')
  }
}

async function remove(row: any) {
  try {
    await projectsApi.removeMember(projectId, row.user_id)
    ElMessage.success('已移除')
    loadMembers()
  } catch (e: any) {
    ElMessage.error('移除失败')
  }
}

async function approve(row: any) {
  try {
    await projectsApi.approveMember(projectId, row.user_id)
    ElMessage.success('已批准')
    loadMembers()
  } catch (e: any) {
    ElMessage.error('批准失败')
  }
}

async function reject(row: any) {
  try {
    await projectsApi.rejectMember(projectId, row.user_id)
    ElMessage.success('已拒绝')
    loadMembers()
  } catch (e: any) {
    ElMessage.error('拒绝失败')
  }
}
</script>

<style scoped>
.project-settings-page {
  padding: 24px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
