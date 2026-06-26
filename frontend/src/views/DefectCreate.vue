<template>
  <div class="defect-create-page">
    <div class="page-header"></div>

    <el-card shadow="never">
      <template #header>
        <div style="font-weight:600;">新建缺陷</div>
      </template>

      <el-form :model="form" label-position="top" style="max-width:800px;">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="简要描述缺陷" />
        </el-form-item>

        <el-form-item label="描述">
          <VditorEditor v-model="form.description" />
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

        <el-form-item label="所属项目" required>
          <el-select v-model="form.project_id" style="width:100%;" placeholder="选择项目">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="负责人（多人用逗号分隔）" required>
          <el-input v-model="assigneesInput" placeholder="用户ID，多人用逗号分隔" />
        </el-form-item>

        <el-divider content-position="left">关联信息（非必填）</el-divider>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="关联需求">
              <el-input v-model="form.requirement_id" placeholder="需求ID" />
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
            <el-form-item label="关联迭代">
              <el-select v-model="form.iteration_id" style="width:100%;" placeholder="选择迭代" clearable>
                <el-option v-for="i in iterations" :key="i.id" :label="i.name" :value="i.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="标签（多个用逗号分隔）">
          <el-input v-model="labelsInput" placeholder="如: UI, 后端, 回归" />
        </el-form-item>

        <el-form-item label="复现步骤">
          <el-input v-model="form.steps_to_reproduce" type="textarea" :rows="4" placeholder="1. ...\n2. ...\n3. ..." />
        </el-form-item>

        <el-form-item label="环境">
          <el-input v-model="form.environment" placeholder="如: Chrome 120 / Windows 11 / iOS 17" />
        </el-form-item>

        <el-form-item>
          <el-button @click="$router.back()">取消</el-button>
          <el-button type="primary" @click="submit" :loading="saving" :disabled="!form.title.trim() || !form.project_id || !assigneesInput.trim()">
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
import { defectsApi, projectsApi, modulesApi, iterationsApi } from '@/api'
import { ElMessage } from 'element-plus'
import VditorEditor from '@/components/VditorEditor.vue'

const router = useRouter()
const projects = ref<any[]>([])
const modules = ref<any[]>([])
const iterations = ref<any[]>([])
const saving = ref(false)
const assigneesInput = ref('')
const labelsInput = ref('')
const form = ref({
  title: '',
  description: '',
  severity: 'major',
  priority: 'p2',
  project_id: '',
  requirement_id: '',
  module_id: null,
  iteration_id: null,
  steps_to_reproduce: '',
  environment: '',
})

const flatModules = computed(() => {
  const out: any[] = []
  const walk = (list: any[], depth: number) => {
    for (const m of list) {
      out.push({ ...m, depth })
      if (m.children?.length) walk(m.children, depth + 1)
    }
  }
  walk(modules.value, 0)
  return out
})

const submit = async () => {
  saving.value = true
  try {
    const data: any = { ...form.value }
    data.assignees = assigneesInput.value.split(',').map((s: string) => s.trim()).filter(Boolean)
    data.labels = labelsInput.value.split(',').map((s: string) => s.trim()).filter(Boolean)
    const res = await defectsApi.create(data)
    ElMessage.success('缺陷已创建')
    router.push(`/defect/${res.data.id}`)
  } catch (e) {
    ElMessage.error('创建失败')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  const [pRes, mRes, iRes] = await Promise.all([
    projectsApi.list(),
    modulesApi.list(),
    iterationsApi.list(),
  ])
  projects.value = pRes.data.items ?? pRes.data
  modules.value = mRes.data
  iterations.value = iRes.data.items ?? iRes.data
})
</script>

<style scoped>
</style>