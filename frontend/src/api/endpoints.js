import api from './client'
export const auth = {
  login: (u, p) => api.post('/api/auth/login/', { username: u, password: p }),
  me: () => api.get('/api/auth/me/'),
}
export const dashboard = {
  metrics: () => api.get('/api/dashboard/'),
  batches: () => api.get('/api/batches/'),
}
export const review = {
  list: (params = {}) => api.get('/api/review/', { params }),
  detail: (id) => api.get(`/api/review/${id}/`),
  edit: (id, data) => api.patch(`/api/review/${id}/edit/`, data),
}
export const actions = {
  approve: (record_ids, note = '') => api.post('/api/approve/', { record_ids, note }),
  reject: (record_ids, note) => api.post('/api/reject/', { record_ids, note }),
}
export const upload = {
  ingest: (file, source_type, onProgress) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('source_type', source_type)
    return api.post('/api/upload/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: e => onProgress?.(Math.round(e.loaded * 100 / e.total)),
    })
  },
}