<template>
  <div class="requirement-create">
    <div class="create-form">
      <div class="form-section">
        <div class="section-title">基本信息</div>
        <div class="form-row">
          <div class="form-item">
            <label class="form-label">需求标题 <span class="required">*</span></label>
            <el-input v-model="form.title" placeholder="请输入需求标题" maxlength="200" show-word-limit />
          </div>
        </div>
        <div class="form-row two-cols">
          <div class="form-item">
            <label class="form-label">所属项目 <span class="required">*</span></label>
            <el-select v-model="form.project_id" placeholder="请选择项目" style="width:100%" @change="onProjectChange">
              <el-option v-for="proj in projects" :key="proj.id" :label="proj.name" :value="proj.id" />
            </el-select>
          </div>
          <div class="form-item">
            <label class="form-label">关联迭代</label>
            <el-select v-model="form.iteration_id" placeholder="请选择迭代" style="width:100%">
              <el-option v-for="iter in filteredIterations" :key="iter.id" :label="iter.name" :value="iter.id" />
            </el-select>
          </div>
        </div>
      </div>

      <div class="form-section">
        <div class="section-title">需求内容</div>
        <div class="form-item">
          <label class="form-label">需求描述</label>
          <VditorEditor
            v-model="form.description"
            placeholder="请输入需求描述，支持 Markdown 格式"
            height="300px"
          />
        </div>
      </div>

      <div class="form-section">
        <div class="section-title">验收标准</div>
        <div class="criteria-list">
          <div v-for="(item, idx) in form.criteriaList" :key="idx" class="criteria-item">
            <span class="criteria-num">{{ idx + 1 }}</span>
            <el-input v-model="form.criteriaList[idx]" placeholder="请输入验收标准" />
            <el-button text type="danger" @click="removeCriteria(idx)" :disabled="form.criteriaList.length <= 1">×</el-button>
          </div>
        </div>
        <el-button text type="primary" @click="addCriteria" class="add-criteria-btn">+ 添加验收标准</el-button>
      </div>

      <div class="form-section">
        <div class="section-title">附件</div>
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="10"
          :on-change="onFileChange"
          :on-remove="onFileRemove"
          multiple
          drag
        >
          <div class="upload-content">
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">将文件拖到此处，或 <em>点击上传</em></div>
            <div class="upload-hint">最多上传 10 个文件，单个文件不超过 100MB</div>
          </div>
        </el-upload>
        <div v-if="form.uploadedFiles.length" class="file-list">
          <div v-for="(f, i) in form.uploadedFiles" :key="i" class="file-item">
            <el-icon><Document /></el-icon>
            <span class="file-name">{{ f.name }}</span>
            <span class="file-size">{{ (f.size / 1024).toFixed(1) }} KB</span>
            <el-button text type="danger" size="small" @click="removeFile(i)">移除</el-button>
          </div>
        </div>
      </div>

      <div class="form-section">
        <div class="section-title">其他信息</div>
        <div class="form-row two-cols">
          <div class="form-item">
            <label class="form-label">优先级</label>
            <el-radio-group v-model="form.priority" class="priority-group">
              <el-radio-button value="P0">P0 紧急</el-radio-button>
              <el-radio-button value="P1">P1 高</el-radio-button>
              <el-radio-button value="P2">P2 中</el-radio-button>
              <el-radio-button value="P3">P3 低</el-radio-button>
            </el-radio-group>
          </div>
          <div class="form-item">
            <label class="form-label">截止日期</label>
            <el-date-picker v-model="form.due_date" type="date" placeholder="选择日期" style="width:200px" value-format="YYYY-MM-DD" />
          </div>
        </div>
      </div>

      <div class="form-actions">
        <el-button @click="$router.push('/requirements')">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="!canSubmit" @click="submitRequirement">创建需求</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { requirementsApi, iterationsApi, projectsApi, attachmentsApi } from '@/api'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document } from '@element-plus/icons-vue'
import VditorEditor from '@/components/VditorEditor.vue'

const projects = ref<any[]>([])
const iterations = ref<any[]>([])
const submitting = ref(false)

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
  if (!form.value.project_id) return []
  return iterations.value.filter((i: any) => i.project_id === form.value.project_id)
})

const canSubmit = computed(() => {
  return form.value.title.trim() && form.value.project_id
})

const onProjectChange = () => {
  form.value.iteration_id = ''
}

const addCriteria = () => {
  form.value.criteriaList.push('')
}

const removeCriteria = (idx: number) => {
  if (form.value.criteriaList.length > 1) {
    form.value.criteriaList.splice(idx, 1)
  }
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
  if (!canSubmit.value) return
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
    window.location.href = `/requirement/${requirementId}`
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
.requirement-create {
  max-width: 900px;
  margin: 0 auto;
}

.create-form {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.form-section {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f1f5;
}

.form-section:last-of-type {
  border-bottom: none;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2329;
  margin-bottom: 16px;
}

.form-row {
  margin-bottom: 16px;
}

.form-row.two-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  color: #4b5059;
}

.required {
  color: #f56c6c;
}

.criteria-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.criteria-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.criteria-num {
  width: 24px;
  height: 24px;
  background: #f5f7ff;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #6366f1;
  flex-shrink: 0;
}

.add-criteria-btn {
  padding: 0;
  font-size: 13px;
}

.upload-content {
  padding: 24px;
  text-align: center;
}

.upload-icon {
  font-size: 32px;
  color: #c0c4cc;
  margin-bottom: 8px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
}

.upload-text em {
  color: #6366f1;
  font-style: normal;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.file-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7ff;
  border-radius: 4px;
  font-size: 13px;
}

.file-item .file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-item .file-size {
  color: #909399;
}

.priority-group {
  display: flex;
  gap: 8px;
}

.form-actions {
  padding: 16px 24px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #fafafa;
  border-top: 1px solid #f0f1f5;
  border-radius: 0 0 8px 8px;
}
</style>