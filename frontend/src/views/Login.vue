<template>
  <div class="login-page">
    <el-card class="login-card" shadow="never">
      <div class="login-logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">CodeSeer</span>
      </div>
      <h2 class="login-title">登录</h2>

      <el-form :model="form" @submit.prevent="handleLogin" label-position="top">
        <el-form-item label="账号">
          <el-input v-model="form.email" placeholder="输入账号" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="••••••••" autocomplete="current-password" show-password />
        </el-form-item>

        <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon :closable="false" style="margin-bottom:16px;" />

        <el-button type="primary" native-type="submit" :loading="loading" style="width:100%;">
          {{ loading ? '登录中…' : '登录' }}
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({ email: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.login(form.value.email, form.value.password)
    router.push('/')
  } catch {
    errorMsg.value = '邮箱或密码错误'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  padding: 20px;
}
.login-card {
  width: 100%;
  max-width: 480px;
  padding: 32px;
  border-radius: 16px;
}
.login-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
}
.logo-icon { font-size: 32px; }
.logo-text { font-size: 24px; font-weight: 700; color: #111827; }
.login-title {
  font-size: 22px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 28px;
}
</style>
