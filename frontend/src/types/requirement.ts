export interface RequirementFormData {
  title: string
  project_id: string
  iteration_id?: string
  description: string
  criteriaList: string[]
  priority: 'P0' | 'P1' | 'P2' | 'P3'
  due_date?: string
  uploadedFiles: File[]
}