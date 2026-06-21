<template>
  <div class="users-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">用户与角色</h1>
        <p class="page-subtitle">管理平台用户、分配角色、配置权限</p>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon> 邀请用户
      </el-button>
    </div>

    <el-card shadow="never" body-style="padding:0;">
      <el-table :data="users" stripe>
        <el-table-column label="用户" min-width="200">
          <template #default="{ row }">
            <div style="display:flex; align-items:center; gap:10px;">
              <div class="user-avatar" :style="{ background: row.avatar_color }">{{ row.name.slice(0, 1) }}</div>
              <span style="font-weight:500;">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180">
          <template #default="{ row }">
            <el-text type="info">{{ row.email }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '活跃' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="120">
          <template #default="{ row }">
            <el-text type="info">{{ row.created_at ? new Date(row.created_at).toLocaleDateString('zh-CN') : '-' }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="right">
          <template #default="{ row }">
            <el-button text size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button text size="small" type="danger" @click="deleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never" style="margin-top:16px;">
      <template #header>
        <div style="font-weight:600;">角色权限矩阵</div>
      </template>
      <el-table :data="rolePermissionsTable" stripe size="small">
        <el-table-column prop="role" label="角色" width="160">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.key)" size="small">{{ row.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权限">
          <template #default="{ row }">
            <div style="display:flex; flex-wrap:wrap; gap:4px;">
              <el-tag v-for="p in row.permissions" :key="p" size="small" type="info">{{ p }}</el-tag>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showForm" :title="editing ? '编辑用户' : '邀请用户'" width="480px">
      <el-form :model="form" label-position="top">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" placeholder="如：张三" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="form.email" placeholder="user@company.com" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%;">
            <el-option v-for="r in roleOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="editing ? '密码（留空不修改）' : '密码'">
          <el-input v-model="form.password" type="password" placeholder="••••••••" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeForm">取消</el-button>
        <el-button type="primary" :loading="saving" :disabled="!form.name.trim() || !form.email.trim()" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usersApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const users = ref<any[]>([])
const rolePermissions = ref<Record<string, string[]>>({})
const showForm = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const form = ref({ name: '', email: '', role: 'developer', password: '' })

const roleOptions = [
  { value: 'admin', label: '管理员（所有权限）' },
  { value: 'product_manager', label: '产品经理' },
  { value: 'project_manager', label: '项目经理' },
  { value: 'developer', label: '开发者' },
  { value: 'viewer', label: '访客' },
]

const rolePermissionsTable = computed(() =>
  Object.entries(rolePermissions.value).map(([key, perms]) => ({
    key,
    label: roleLabel(key),
    permissions: perms,
  }))
)

const roleTagType = (r: string) => ({
  admin: 'danger', product_manager: '', project_manager: 'primary',
  developer: 'success', viewer: 'info',
}[r] || 'info')

const roleLabel = (r: string) => ({
  admin: '管理员', product_manager: '产品经理', project_manager: '项目经理',
  developer: '开发者', viewer: '访客',
}[r] || r)

const openCreate = () => {
  editing.value = null
  form.value = { name: '', email: '', role: 'developer', password: '' }
  showForm.value = true
}

const openEdit = (u: any) => {
  editing.value = u
  form.value = { name: u.name, email: u.email, role: u.role, password: '' }
  showForm.value = true
}

const closeForm = () => { showForm.value = false }

const saveUser = async () => {
  saving.value = true
  try {
    if (editing.value) {
      const payload: any = { name: form.value.name, role: form.value.role }
      if (form.value.password) payload.password = form.value.password
      await usersApi.update(editing.value.id, payload)
    } else {
      await usersApi.create(form.value)
    }
    closeForm()
    ElMessage.success('保存成功')
    fetchData()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

const deleteUser = async (u: any) => {
  try {
    await ElMessageBox.confirm(`删除用户「${u.name}」？`, '提示', { type: 'warning' })
    await usersApi.delete(u.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

const fetchData = async () => {
  try {
    const [uRes, pRes] = await Promise.all([usersApi.list(), usersApi.rolePermissions()])
    users.value = uRes.data
    rolePermissions.value = pRes.data
  } catch (e) { console.error(e) }
}

onMounted(fetchData)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-title { font-size: 20px; font-weight: 700; color: #1f2329; margin: 0; }
.page-subtitle { font-size: 13px; color: #969ba4; margin: 4px 0 0 0; }
.user-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  color: white; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
</style>
