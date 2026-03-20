import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 300000 }) // 5분 타임아웃

export const filesAPI = {
  upload: (fileType, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post(`/files/upload/${fileType}`, fd)
  },
  status: () => api.get('/files/status'),
}

export const questionsAPI = {
  previewMapping: (competencyNo) =>
    api.post('/questions/preview-mapping', null, { params: { competency_no: competencyNo } }),
  generate: (payload) => api.post('/questions/generate', payload),
  list: (params) => api.get('/questions/list', { params }),
  get: (id) => api.get(`/questions/${id}`),
  update: (id, data) => api.put(`/questions/${id}`, data),
  delete: (id) => api.delete(`/questions/${id}`),
  exportSelected: (ids) =>
    api.post('/questions/export', ids, { responseType: 'blob' }),
  exportAll: () =>
    api.post('/questions/export-all', null, { responseType: 'blob' }),
}

export const analysisAPI = {
  upload: (file, examName) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/analysis/upload', fd, { params: { exam_name: examName } })
  },
  list: () => api.get('/analysis/list'),
  get: (id) => api.get(`/analysis/${id}`),
}

export default api
