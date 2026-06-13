<template>
  <div class="users-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">用户与角色</h1>
        <p class="page-subtitle">管理平台用户、分配角色、配置权限</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <span>＋</span> 邀请用户
      </button>
    </div>

    <div class="card" style="padding:0; overflow:hidden;">
      <table class="table">
        <thead>
          <tr>
            <th>用户</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>状态</th>
            <th>创建时间</th>
            <th style="width:160px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>
              <div style="display:flex; align-items:center; gap:10px;">
                <div class="user-avatar" :style="{ background: u.avatar_color }">{{ u.name.slice(0, 1) }}</div>
                <span style="font-weight:500;">{{ u.name }}</span>
              </div>
            </td>
            <td class="text-muted text-small">{{ u.email }}</td>
            <td>
              <span :class="['role-badge', u.role]">{{ roleLabel(u.role) }}</span>
            </td>
            <td>
              <span :class="['status-badge', u.is_active ? 'active' : 'inactive']">
                {{ u.is_active ? '活跃' : '禁用' }}
              </span>
            </td>
            <td class="text-muted text-small">{{ u.created_at ? new Date(u.created_at).toLocaleDateString('zh-CN') : '-' }}</td>
            <td>
              <div class="action-row">
                <button class="btn-link" @click="openEdit(u)">编辑</button>
                <button class="btn-link danger" @click="deleteUser(u)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="6">
              <div class="empty-state">
                <div class="empty-state-icon">☉</div>
                <div class="empty-state-text">还没有用户，点击「邀请用户」开始</div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Role permissions card -->
    <div class="card" style="margin-top:16px;">
      <div class="card-title">角色权限矩阵</div>
      <table class="table">
        <thead>
          <tr>
            <th>角色</th>
            <th>权限</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(perms, role) in rolePermissions" :key="role">
            <td style="font-weight:600; vertical-align:top; width:140px;">
              <span :class="['role-badge', role]">{{ roleLabel(role) }}</span>
            </td>
            <td>
              <div class="perm-tags">
                <span v-for="p in perms" :key="p" class="perm-tag">{{ p }}</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal" style="width:480px;">
        <div class="modal-header">
          <h3>{{ editing ? '编辑用户' : '邀请用户' }}</h3>
          <button class="modal-close" @click="closeForm">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">姓名 <span class="required">*</span></label>
            <input v-model="form.name" class="form-input" placeholder="如：张三" autofocus />
          </div>
          <div class="form-group">
            <label class="form-label">邮箱 <span class="required">*</span></label>
            <input v-model="form.email" class="form-input" placeholder="user@company.com" :disabled="!!editing" />
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label class="form-label">角色</label>
            <select v-model="form.role" class="form-input">
              <option v-for="r in roleOptions" :key="r.value" :value="r.value">{{ r.label }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeForm">取消</button>
          <button class="btn btn-primary" :disabled="!form.name.trim() || !form.email.trim() || saving" @click="saveUser">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usersApi } from '@/api'

const users = ref<any[]>([])
const rolePermissions = ref<Record<string, string[]>>({})
const showForm = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const form = ref({ name: '', email: '', role: 'developer' })

const roleOptions = [
  { value: 'admin', label: '管理员（所有权限）' },
  { value: 'product_manager', label: '产品经理' },
  { value: 'project_manager', label: '项目经理' },
  { value: 'developer', label: '开发者' },
  { value: 'viewer', label: '访客' },
]

const roleLabel = (r: string) => ({
  admin: '管理员', product_manager: '产品经理', project_manager: '项目经理',
  developer: '开发者', viewer: '访客',
}[r] || r)

const openCreate = () => {
  editing.value = null
  form.value = { name: '', email: '', role: 'developer' }
  showForm.value = true
}

const openEdit = (u: any) => {
  editing.value = u
  form.value = { name: u.name, email: u.email, role: u.role }
  showForm.value = true
}

const closeForm = () => { showForm.value = false }

const saveUser = async () => {
  saving.value = true
  try {
    if (editing.value) {
      await usersApi.update(editing.value.id, { name: form.value.name, role: form.value.role })
    } else {
      await usersApi.create(form.value)
    }
    closeForm()
    fetchData()
  } catch (e: any) { alert(e?.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

const deleteUser = async (u: any) => {
  if (!confirm(`删除用户「${u.name}」？`)) return
  try {
    await usersApi.delete(u.id)
    fetchData()
  } catch (e) { console.error(e) }
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
.user-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  color: white; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}

.role-badge {
  font-size: 12px; font-weight: 500;
  padding: 2px 8px; border-radius: 4px;
  display: inline-block;
}
.role-badge.admin            { background: #fee2e2; color: #991b1b; }
.role-badge.product_manager  { background: #ede9fe; color: #5b21b6; }
.role-badge.project_manager  { background: #dbeafe; color: #1e40af; }
.role-badge.developer        { background: #d1fae5; color: #065f46; }
.role-badge.viewer           { background: #f3f4f6; color: #6b7280; }

.status-badge.active   { background: #d1fae5; color: #065f46; }
.status-badge.inactive { background: #f3f4f6; color: #6b7280; }

.action-row { display: flex; gap: 12px; }
.btn-link {
  background: none; border: none; cursor: pointer;
  color: #6366f1; font-size: 13px; padding: 0;
}
.btn-link:hover { text-decoration: underline; }
.btn-link.danger { color: #dc2626; }

.perm-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.perm-tag {
  font-family: monospace; font-size: 11px;
  background: #f3f4f6; color: #374151;
  padding: 2px 6px; border-radius: 4px;
}
</style>
