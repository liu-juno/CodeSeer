<template>
  <div class="defect-create-page">
    <el-card shadow="never">
      <template #header>
        <div style="font-weight:600;">新建缺陷</div>
      </template>

      <el-form :model="form" label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="简要描述缺陷" />
        </el-form-item>

        <el-form-item label="描述">
          <VditorEditor v-model="form.description" placeholder="详细描述缺陷现象，支持 Markdown..." :height="300" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="严重程度">
              <el-select v-model="form.severity" style="width:100%;">
                <el-option value="fatal" label="致命" />
                <el-option value="critical" label="严重" />
                <el-option value="major" label="一般" />
                <el-option value="minor" label="轻微" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="form.priority" style="width:100%;">
                <el-option value="p0" label="P0 - 紧急" />
                <el-option value="p1" label="P1 - 重要" />
                <el-option value="p2" label="P2 - 一般" />
                <el-option value="p3" label="P3 - 低" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="负责人">
          <el-select v-model="form.assignees" multiple style="width:100%;" placeholder="选择负责人（可多选）" filterable>
            <el-option v-for="u in users" :key="u.id" :value="u.id" :label="u.name">
              <div style="display:flex;align-items:center;gap:8px;">
                <span :style="`width:22px;height:22px;border-radius:50%;background:${u.avatar_color||'#6366f1'};display:flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:600;`">
                  {{ (u.name||'?')[0].toUpperCase() }}
                </span>
                <span>{{ u.name }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-divider content-position="left">关联信息（非必填）</el-divider>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="关联迭代">
              <el-select v-model="form.iteration_id" style="width:100%;" placeholder="选择迭代" clearable>
                <el-option v-for="i in iterations" :key="i.id" :label="i.name" :value="i.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="关联模块">
              <el-select v-model="form.module_id" style="width:100%;" placeholder="选择模块" clearable>
                <el-option v-for="m in flatModules" :key="m.id" :label="m.path + m.name" :value="m.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="标签（逗号分隔）">
              <el-input v-model="labelsInput" placeholder="如: UI, 后端, 回归" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="复现步骤">
          <el-input v-model="form.steps_to_reproduce" type="textarea" :rows="4" placeholder="1. 打开页面&#10;2. 点击...&#10;3. 观察到..." />
        </el-form-item>

        <el-form-item label="环境">
          <el-input v-model="form.environment" placeholder="如: Chrome 120 / Windows 11 / iOS 17" />
        </el-form-item>

        <el-form-item>
          <el-button @click="$router.back()">取消</el-button>
          <el-button type="primary" :loading="saving" :disabled="!form.title.trim()" @click="submit">
            创建缺陷
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { defectsApi, modulesApi, iterationsApi, usersApi } from '@/api'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'
import VditorEditor from '@/components/VditorEditor.vue'

const router = useRouter()
const projectStore = useProjectStore()

const modules = ref<any[]>([])
const iterations = ref<any[]>([])
const users = ref<any[]>([])
const saving = ref(false)
const labelsInput = ref('')

const form = ref({
  title: '',
  description: '',
  severity: 'major',
  priority: 'p2',
  assignees: [] as string[],
  requirement_id: '',
  module_id: null as string | null,
  iteration_id: projectStore.currentIterationId || null as string | null,
  steps_to_reproduce: '',
  environment: '',
})

const flatModules = computed(() => {
  const out: any[] = []
  const walk = (list: any[], prefix: string) => {
    for (const m of list) {
      out.push({ ...m, path: prefix })
      if (m.children?.length) walk(m.children, prefix + m.name + ' / ')
    }
  }
  walk(modules.value, '')
  return out
})

const submit = async () => {
  saving.value = true
  try {
    const data: any = {
      ...form.value,
      project_id: projectStore.currentProjectId,
      labels: labelsInput.value.split(',').map((s: string) => s.trim()).filter(Boolean),
    }
    if (!data.module_id) delete data.module_id
    if (!data.iteration_id) delete data.iteration_id
    if (!data.requirement_id) delete data.requirement_id
    const res = await defectsApi.create(data)
    ElMessage.success('缺陷已创建')
    router.push(`/defects/${res.data.id}`)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  const requests: Promise<any>[] = [modulesApi.list(), usersApi.list()]
  if (projectStore.currentProjectId) {
    requests.push(iterationsApi.byProject(projectStore.currentProjectId))
  }
  const [mRes, uRes, iRes] = await Promise.all(requests)
  modules.value = mRes.data ?? []
  users.value = uRes.data?.items ?? uRes.data ?? []
  if (iRes) {
    iterations.value = Array.isArray(iRes.data) ? iRes.data : (iRes.data?.items ?? [])
  }
})
</script>

<style scoped>
.defect-create-page { width: 100%; }
</style>
