import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('auth_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)

// Auth API
export const authApi = {
  login: (data: { email: string; password: string }) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
}

// Projects API
export const projectsApi = {
  list: (page?: number, pageSize?: number) => {
    const params: any = {}
    if (page !== undefined) params.page = page
    if (pageSize !== undefined) params.page_size = pageSize
    return api.get('/projects', { params })
  },
  get: (id: string) => api.get(`/projects/${id}`),
  create: (data: any) => api.post('/projects', data),
  update: (id: string, data: any) => api.put(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  statistics: (id: string) => api.get(`/projects/${id}/statistics`),
}

// Iterations API
export const iterationsApi = {
  list: (page?: number, pageSize?: number) => {
    const params: any = {}
    if (page !== undefined) params.page = page
    if (pageSize !== undefined) params.page_size = pageSize
    return api.get('/iterations', { params })
  },
  get: (id: string) => api.get(`/iterations/${id}`),
  create: (data: any) => api.post('/iterations', data),
  update: (id: string, data: any) => api.put(`/iterations/${id}`, data),
  delete: (id: string) => api.delete(`/iterations/${id}`),
  byProject: (projectId: string) => api.get(`/iterations/by-project/${projectId}`),
  release: (id: string) => api.post(`/iterations/${id}/release`),
  statistics: (id: string) => api.get(`/iterations/${id}/statistics`),
}

// Requirements API
export const requirementsApi = {
  list: (params?: any) => api.get('/requirements', { params }),
  get: (id: string) => api.get(`/requirements/${id}`),
  create: (data: any) => api.post('/requirements', data),
  update: (id: string, data: any) => api.put(`/requirements/${id}`, data),
  delete: (id: string) => api.delete(`/requirements/${id}`),
  assign: (id: string, assigneeId: string, comment?: string) => api.post(`/requirements/${id}/assign`, { assignee_id: assigneeId, comment }),
  transition: (id: string, action: string, comment?: string) => api.post(`/requirements/${id}/transition`, { action, comment }),
  byIteration: (iterationId: string) => api.get(`/requirements/by-iteration/${iterationId}`),
  phases: (id: string) => api.get(`/requirements/${id}/phases`),
  updatePhase: (id: string, phaseId: string, data: any) => api.put(`/requirements/${id}/phases/${phaseId}`, data),
  history: (id: string) => api.get(`/requirements/${id}/history`),
}

// Tasks API
export const tasksApi = {
  list: (requirementId: string) => api.get(`/requirements/${requirementId}/tasks`),
  create: (requirementId: string, data: any) => api.post(`/requirements/${requirementId}/tasks`, data),
  update: (requirementId: string, taskId: string, data: any) => api.put(`/requirements/${requirementId}/tasks/${taskId}`, data),
  delete: (requirementId: string, taskId: string) => api.delete(`/requirements/${requirementId}/tasks/${taskId}`),
}

// Test Records API
export const testRecordsApi = {
  list: (requirementId: string) => api.get(`/requirements/${requirementId}/test-records`),
  create: (requirementId: string, data: any) => api.post(`/requirements/${requirementId}/test-records`, data),
}

// Documents API
export const documentsApi = {
  list: (params?: any) => api.get('/documents', { params }),
  get: (id: string) => api.get(`/documents/${id}`),
  create: (data: any) => api.post('/documents', data),
  update: (id: string, data: any) => api.put(`/documents/${id}`, data),
  delete: (id: string) => api.delete(`/documents/${id}`),
  archive: (id: string) => api.post(`/documents/${id}/archive`),
  process: (id: string) => api.post(`/documents/${id}/process`),
  versions: (id: string) => api.get(`/documents/${id}/versions`),
}

// Modules API
export const modulesApi = {
  list: (params?: any) => api.get('/modules', { params }),
  get: (id: string) => api.get(`/modules/${id}`),
  create: (data: any) => api.post('/modules', data),
  update: (id: string, data: any) => api.put(`/modules/${id}`, data),
  delete: (id: string) => api.delete(`/modules/${id}`),
  documents: (id: string) => api.get(`/modules/${id}/documents`),
  knowledge: (id: string) => api.get(`/modules/${id}/knowledge`),
  generateSkill: (id: string, data: { name: string; description?: string; document_ids: string[] }) => api.post(`/modules/${id}/generate-skill`, data),
  deleteSkill: (id: string) => api.delete(`/modules/${id}/skill`),
}

// Webhooks API
export const webhooksApi = {
  list: () => api.get('/webhooks'),
  get: (id: string) => api.get(`/webhooks/${id}`),
  create: (data: any) => api.post('/webhooks', data),
  update: (id: string, data: any) => api.put(`/webhooks/${id}`, data),
  delete: (id: string) => api.delete(`/webhooks/${id}`),
  test: (id: string) => api.post(`/webhooks/${id}/test`),
  deliveries: (id: string) => api.get(`/webhooks/${id}/deliveries`),
}

// Users API
export const usersApi = {
  list: () => api.get('/users'),
  create: (data: any) => api.post('/users', data),
  update: (id: string, data: any) => api.put(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
  rolePermissions: () => api.get('/users/roles/permissions'),
}

// Config API (state machine + custom fields)
export const configApi = {
  stateMachine: () => api.get('/config/state-machine'),
  updateStateMachine: (states: any[]) => api.put('/config/state-machine', states),
  customFields: () => api.get('/config/custom-fields'),
  createCustomField: (data: any) => api.post('/config/custom-fields', data),
  updateCustomField: (id: string, data: any) => api.put(`/config/custom-fields/${id}`, data),
  deleteCustomField: (id: string) => api.delete(`/config/custom-fields/${id}`),
  requirementStatusConfig: () => api.get('/requirements/status-config'),
}

// MCP Tokens API
export const mcpTokensApi = {
  list: (userId: string) => api.get('/mcp/tokens', { params: { user_id: userId } }),
  create: (data: { name: string; user_id: string; days?: number }) => api.post('/mcp/tokens', data),
  delete: (id: string, userId: string) => api.delete(`/mcp/tokens/${id}`, { params: { user_id: userId } }),
}

// Attachments API
export const attachmentsApi = {
  upload: (requirementId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/requirements/${requirementId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  list: (requirementId: string) =>
    api.get(`/requirements/${requirementId}/attachments`),
  download: (requirementId: string, attachmentId: string) =>
    api.get(`/requirements/${requirementId}/attachments/${attachmentId}/download`, {
      responseType: 'blob',
    }),
  delete: (requirementId: string, attachmentId: string) =>
    api.delete(`/requirements/${requirementId}/attachments/${attachmentId}`),
}

export default api