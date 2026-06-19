<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">CodeSeer</span>
      </div>
      <h2 class="login-title">登录</h2>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label class="form-label">账号</label>
          <input
            v-model="email"
            type="text"
            class="form-input"
            placeholder="输入账号"
            required
            autocomplete="username"
          />
        </div>
        <div class="form-group">
          <label class="form-label">密码</label>
          <input
            v-model="password"
            type="password"
            class="form-input"
            placeholder="••••••••"
            required
            autocomplete="current-password"
          />
        </div>

        <p v-if="errorMsg" class="login-error">{{ errorMsg }}</p>

        <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.login(email.value, password.value)
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
}

.login-card {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  width: 360px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
}

.logo-icon { font-size: 24px; }
.logo-text { font-size: 20px; font-weight: 700; color: #111827; }

.login-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 24px;
}

.login-form { display: flex; flex-direction: column; gap: 16px; }

.form-group { display: flex; flex-direction: column; gap: 6px; }

.form-label { font-size: 13px; font-weight: 500; color: #374151; }

.form-input {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.form-input:focus { border-color: #6366f1; }

.login-error {
  font-size: 13px;
  color: #ef4444;
  margin: 0;
}

.login-btn {
  width: 100%;
  padding: 10px;
  margin-top: 4px;
  background: #6366f1;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.login-btn:hover:not(:disabled) { background: #4f46e5; }
.login-btn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
