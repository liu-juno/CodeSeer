<template>
  <div class="project-select-page">
    <div class="page-header">
      <h2>选择项目</h2>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="我的项目" name="mine">
        <div v-if="myProjects.length === 0" class="empty-tip">
          暂无参与的项目
        </div>
        <div v-else class="project-grid">
          <div
            v-for="project in myProjects"
            :key="project.id"
            class="project-card"
            @click="enterProject(project)"
          >
            <div class="project-icon">{{ project.name.charAt(0) }}</div>
            <div class="project-name">{{ project.name }}</div>
            <div class="project-desc">{{ project.description || '暂无描述' }}</div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="全部项目" name="all">
        <div class="project-grid">
          <div
            v-for="project in allProjects"
            :key="project.id"
            class="project-card"
          >
            <div class="project-icon">{{ project.name.charAt(0) }}</div>
            <div class="project-name">{{ project.name }}</div>
            <div class="project-desc">{{ project.description || '暂无描述' }}</div>
            <div class="project-actions">
              <template v-if="isMyProject(project.id)">
                <el-button type="primary" size="small" @click="enterProject(project)">
                  进入
                </el-button>
              </template>
              <template v-else-if="isPending(project.id)">
                <el-tag type="warning">待审核</el-tag>
              </template>
              <template v-else>
                <el-button type="outline" size="small" @click="applyToProject(project)">
                  申请加入
                </el-button>
              </template>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'

const router = useRouter()
const projectStore = useProjectStore()

const activeTab = ref('mine')
const myProjects = ref<any[]>([])
const allProjects = ref<any[]>([])
const pendingProjects = ref<Set<string>>(new Set())

onMounted(async () => {
  await loadProjects()
})

async function loadProjects() {
  myProjects.value = await projectStore.fetchMyProjects()
  const res = await projectsApi.list(1, 100)
  allProjects.value = res.data.items || res.data
}

function isMyProject(projectId: string): boolean {
  return myProjects.value.some(p => p.id === projectId)
}

function isPending(projectId: string): boolean {
  return pendingProjects.value.has(projectId)
}

async function applyToProject(project: any) {
  try {
    await projectsApi.applyToProject(project.id)
    ElMessage.success('申请已提交，请等待审核')
    pendingProjects.value.add(project.id)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '申请失败')
  }
}

function enterProject(project: any) {
  projectStore.setCurrentProject(project)
  router.push('/dashboard')
}
</script>

<style scoped>
.project-select-page {
  padding: 24px;
}
.page-header {
  margin-bottom: 24px;
}
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.project-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.project-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.project-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: #6366f1;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 12px;
}
.project-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}
.project-desc {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
}
.empty-tip {
  text-align: center;
  padding: 48px;
  color: #9ca3af;
}
</style>
