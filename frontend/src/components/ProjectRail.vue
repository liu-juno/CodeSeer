<template>
  <nav class="project-rail">
    <div class="rail-logo" @click="$router.push('/projects')">
      <span class="logo-abbr">CS</span>
    </div>

    <div class="rail-projects">
      <el-tooltip
        v-for="project in projects"
        :key="project.id"
        :content="project.name"
        placement="right"
        :show-after="300"
      >
        <div
          :class="['project-icon', { active: project.id === currentProjectId }]"
          @click="$emit('select-project', project)"
        >
          {{ project.name.charAt(0).toUpperCase() }}
        </div>
      </el-tooltip>
    </div>

    <div class="rail-footer">
      <el-tooltip content="创建项目" placement="right">
        <div class="create-btn" @click="$emit('create-project')">+</div>
      </el-tooltip>
    </div>
  </nav>
</template>

<script setup lang="ts">
defineProps<{
  projects: any[]
  currentProjectId: string | null
}>()

defineEmits<{
  (e: 'select-project', project: any): void
  (e: 'create-project'): void
}>()
</script>

<style scoped>
.project-rail {
  width: var(--rail-width);
  background: var(--rail-bg);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  overflow: hidden;
}

.rail-logo {
  width: 100%;
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border-default);
  cursor: pointer;
  flex-shrink: 0;
}

.logo-abbr {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 0.05em;
}

.rail-projects {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 0;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
}

.project-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  background: var(--bg-hover);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
  user-select: none;
}

.project-icon:hover,
.project-icon.active {
  background: var(--color-primary);
  color: #fff;
}

.rail-footer {
  padding: 0.75rem 0;
  border-top: 1px solid var(--border-default);
  width: 100%;
  display: flex;
  justify-content: center;
  flex-shrink: 0;
}

.create-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  border: 1.5px dashed var(--border-default);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.create-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
</style>
