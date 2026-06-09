import api from './client'

export const getFirearms = (includeInactive = false) =>
  api.get('/api/firearms/', { params: { include_inactive: includeInactive } })

export const getFirearm = (id) => api.get(`/api/firearms/${id}`)
export const createFirearm = (data) => api.post('/api/firearms/', data)
export const updateFirearm = (id, data) => api.put(`/api/firearms/${id}`, data)
export const deleteFirearm = (id) => api.delete(`/api/firearms/${id}`)
