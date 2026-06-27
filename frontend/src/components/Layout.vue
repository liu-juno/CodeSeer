<template>
  <div class="app-shell">
    <ProjectRail
      :projects="projectStore.myProjects"
      :current-project-id="projectStore.currentProjectId"
      @select-project="onSelectProject"
      @create-project="router.push('/projects')"
    />
    <ModuleSidebar />
    <div class="main-area">
      <AppTopbar />
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import ProjectRail from '@/components/ProjectRail.vue'
import ModuleSidebar from '@/components/ModuleSidebar.vue'
import AppTopbar from '@/components/AppTopbar.vue'

const router = useRouter()
const projectStore = useProjectStore()

onMounted(async () => {
  await projectStore.fetchMyProjects()
})

function onSelectProject(project: any) {
  projectStore.setCurrentProject(project)
  router.push('/dashboard')
}
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--bg-base);
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: clamp(16px, 2vw, 28px);
  background: var(--bg-base);
}
</style>
