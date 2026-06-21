<template>
  <div class="requirement-create-page">
    <div class="page-header">
      <el-button text @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <h1 class="page-title">创建需求</h1>
    </div>

    <el-card shadow="never" class="form-card">
      <el-steps :active="currentStep" finish-status="success" style="margin-bottom:32px;">
        <el-step v-for="(s, i) in steps" :key="i" :title="s" />
      </el-steps>

      <el-form :model="form" label-position="top">
        <div v-show="currentStep === 0">
          <el-form-item label="需求标题" required>
            <el-input v-model="form.title" placeholder="用一句话描述这个需求..." maxlength="200" show-word-limit />
          </el-form-item>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px;">
            <el-form-item label="所属项目" required>
              <el-select v-model="form.project_id" placeholder="选择项目" style="width:100%" @change="onProjectChange">
                <el-option v-for="proj in projects" :key="proj.id" :label="proj.name" :value="proj.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="关联迭代">
              <el-select v-model="form.iteration_id" placeholder="选择迭代" style="width:100%">
                <el-option v-for="iter in filteredIterations" :key="iter.id" :label="iter.name" :value="iter.id" />
              </el-select>
            </el-form-item>
          </div>
        </div>

        <div v-show="currentStep === 1">
          <el-form-item label="需求描述">
            <VditorEditor
              v-model="form.description"
              placeholder="请输入需求描述，支持 Markdown 格式"
              height="400px"
            />
          </el-form-item>
          <el-form-item label="验收标准">
            <div v-for="(item, idx) in form.criteriaList" :key="idx" style="display:flex; gap:8px; margin-bottom:8px;">
              <el-input v-model="form.criteriaList[idx]" :placeholder="`验收条件 ${idx + 1}`" style="flex:1;" />
              <el-button text type="danger" @click="removeCriteria(idx)">×</el-button>
            </div>
            <el-button text type="primary" @click="addCriteria">+ 添加验收标准</el-button>
          </el-form-item>
          <el-form-item label="附件上传">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :limit="10"
              :on-change="onFileChange"
              :on-remove="onFileRemove"
              multiple
              drag
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
              <template #tip>
                <div class="el-upload__tip">最多上传 10 个文件，单个文件不超过 100MB</div>
              </template>
            </el-upload>
            <div v-if="form.uploadedFiles.length" style="margin-top:16px;">
              <div v-for="(f, i) in form.uploadedFiles" :key="i" style="display:flex; align-items:center; gap:8px; margin-bottom:6px; padding:8px; background:#f5f7ff; border-radius:4px;">
                <el-icon><Document /></el-icon>
                <span style="flex:1; font-size:13px;">{{ f.name }}</span>
                <span style="color:#909399; font-size:12px;">{{ (f.size / 1024).toFixed(1) }} KB</span>
                <el-button text type="danger" size="small" @click="removeFile(i)">×</el-button>
              </div>
            </div>
          </el-form-item>
        </div>

        <div v-show="currentStep === 2">
          <el-form-item label="优先级">
            <el-radio-group v-model="form.priority">
              <el-radio-button value="P0">P0 紧急</el-radio-button>
              <el-radio-button value="P1">P1 高</el-radio-button>
              <el-radio-button value="P2">P2 中</el-radio-button>
              <el-radio-button value="P3">P3 低</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="截止日期">
            <el-date-picker v-model="form.due_date" type="date" placeholder="选择日期" style="width:200px" value-format="YYYY-MM-DD" />
          </el-form-item>
        </div>
      </el-form>

      <div class="form-actions">
        <el-button @click="$router.back()">取消</el-button>
        <el-button v-if="currentStep > 0" @click="currentStep--">上一步</el-button>
        <el-button v-if="currentStep < 2" type="primary" :disabled="!canNext" @click="currentStep++">下一步</el-button>
        <el-button v-if="currentStep === 2" type="primary" :loading="submitting" @click="submitRequirement">创建需求</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { requirementsApi, iterationsApi, projectsApi, attachmentsApi } from '@/api'
import { ElMessage } from 'element-plus'
import { ArrowLeft, UploadFilled, Document } from '@element-plus/icons-vue'
import VditorEditor from '@/components/VditorEditor.vue'

const router = useRouter()

const steps = ['基础信息', '需求内容', '设置']
const currentStep = ref(0)
const submitting = ref(false)

const projects = ref<any[]>([])
const iterations = ref<any[]>([])

const DESCRIPTION_TEMPLATE = `## 背景
[描述业务背景和用户痛点]

## 用户故事
作为 [用户角色]，我希望 [功能目标]，以便 [获得价值]。

## 功能说明
[详细描述功能逻辑和交互细节]`

const defaultForm = () => ({
  title: '',
  project_id: '',
  iteration_id: '',
  description: DESCRIPTION_TEMPLATE,
  criteriaList: [''] as string[],
  priority: 'P2',
  due_date: '',
  uploadedFiles: [] as File[],
})

const form = ref(defaultForm())

const filteredIterations = computed(() => {
  if (!form.value.project_id) return iterations.value
  return iterations.value.filter((i: any) => i.project_id === form.value.project_id)
})

const canNext = computed(() => {
  if (currentStep.value === 0) return form.value.title.trim() && form.value.project_id
  return true
})

const onProjectChange = () => {
  form.value.iteration_id = ''
}

const addCriteria = () => {
  form.value.criteriaList.push('')
}

const removeCriteria = (idx: number) => {
  form.value.criteriaList.splice(idx, 1)
  if (!form.value.criteriaList.length) form.value.criteriaList.push('')
}

const uploadRef = ref()
const onFileChange = (file: any) => {
  form.value.uploadedFiles.push(file.raw)
}

const removeFile = (index: number) => {
  form.value.uploadedFiles.splice(index, 1)
}

const onFileRemove = (file: any) => {
  const idx = form.value.uploadedFiles.findIndex((f: any) => f.raw === file.raw)
  if (idx >= 0) form.value.uploadedFiles.splice(idx, 1)
}

const submitRequirement = async () => {
  submitting.value = true
  try {
    const criteria = form.value.criteriaList.filter(c => c.trim()).join('\n')

    const res = await requirementsApi.create({
      title: form.value.title,
      project_id: form.value.project_id,
      iteration_id: form.value.iteration_id || null,
      description: form.value.description,
      acceptance_criteria: criteria,
      priority: form.value.priority,
      due_date: form.value.due_date ? form.value.due_date + 'T00:00:00' : null,
    })

    const requirementId = res.data.id

    for (const file of form.value.uploadedFiles) {
      await attachmentsApi.upload(requirementId, file)
    }

    ElMessage.success('创建成功')
    router.push(`/requirement/${requirementId}`)
  } catch (e) {
    console.error(e)
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const [projRes, iterRes] = await Promise.all([
      projectsApi.list(),
      iterationsApi.list(),
    ])
    projects.value = projRes.data.items
    iterations.value = iterRes.data.items
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.requirement-create-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2329;
  margin: 0;
}

.form-card {
  border-radius: 12px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #f0f1f5;
}
</style>