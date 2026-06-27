<template>
  <div class="project-settings-page">
    <el-link underline="never" type="primary" @click="$router.push('/projects')" style="margin-bottom:16px; display:inline-block;">
      ← 返回项目
    </el-link>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="成员管理" name="members">
        <div class="section-header">
          <h3>项目成员</h3>
          <el-button type="primary" @click="showAddDialog = true">
            添加成员
          </el-button>
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
        <el-form-item label="用户邮箱">
          <el-select v-model="addForm.email" filterable placeholder="选择用户">
            <el-option v-for="user in users" :key="user.id" :label="user.email" :value="user.email" />
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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi, usersApi } from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const projectId = route.params.id as string

const activeTab = ref('members')
const members = ref<any[]>([])
const showAddDialog = ref(false)
const addForm = ref({ email: '', role: 'dev' })
const users = ref<any[]>([])

onMounted(() => {
  loadMembers()
  loadUsers()
})

async function loadMembers() {
  const res = await projectsApi.listMembers(projectId)
  members.value = res.data
}

async function loadUsers() {
  const res = await usersApi.list()
  users.value = res.data || []
}

async function addMember() {
  const user = users.value.find(u => u.email === addForm.value.email)
  if (!user) {
    ElMessage.error('用户不存在')
    return
  }
  try {
    await projectsApi.addMember(projectId, { user_id: user.id, role: addForm.value.role })
    ElMessage.success('添加成功')
    showAddDialog.value = false
    loadMembers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  }
}

async function updateRole(row: any) {
  await projectsApi.updateMember(projectId, row.user_id, { role: row.role })
  ElMessage.success('更新成功')
}

async function remove(row: any) {
  await projectsApi.removeMember(projectId, row.user_id)
  ElMessage.success('已移除')
  loadMembers()
}

async function approve(row: any) {
  await projectsApi.approveMember(projectId, row.user_id)
  ElMessage.success('已批准')
  loadMembers()
}

async function reject(row: any) {
  await projectsApi.rejectMember(projectId, row.user_id)
  ElMessage.success('已拒绝')
  loadMembers()
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
