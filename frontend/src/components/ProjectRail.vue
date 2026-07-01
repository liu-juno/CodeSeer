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
        :show-after="500"
      >
        <div
          :class="['project-item', { active: project.id === currentProjectId }]"
          @click="$emit('select-project', project)"
        >
          <div class="project-avatar" :style="{ background: projectColor(project.name) }">
            {{ abbreviation(project.name) }}
          </div>
          <span class="project-label">{{ project.name }}</span>
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

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6']

function projectColor(name: string): string {
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) & 0xffffffff
  return COLORS[Math.abs(h) % COLORS.length]
}

function abbreviation(name: string): string {
  const caps = name.match(/[A-Z]/g)
  if (caps && caps.length >= 2) return caps.slice(0, 2).join('')
  return name.slice(0, 2)
}
</script>

<style scoped>
.project-rail {
  width: var(--rail-width);
  background: var(--rail-bg);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  flex-shrink: 0;
  overflow: hidden;
}

.rail-logo {
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
  gap: 0.25rem;
  padding: 0.5rem 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.project-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.375rem;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background 0.15s, border-color 0.15s;
  user-select: none;
}

.project-item:hover {
  background: var(--bg-hover);
}

.project-item.active {
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  border-left-color: var(--color-primary);
}

.project-avatar {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
  transition: box-shadow 0.15s;
}

.project-item.active .project-avatar {
  box-shadow: 0 0 0 2px #fff, 0 0 0 4px var(--color-primary);
}

.project-label {
  font-size: 0.625rem;
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.3;
  word-break: break-all;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  width: 100%;
}

.project-item.active .project-label {
  color: var(--color-primary);
  font-weight: 500;
}

.rail-footer {
  padding: 0.75rem 0;
  border-top: 1px solid var(--border-default);
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
