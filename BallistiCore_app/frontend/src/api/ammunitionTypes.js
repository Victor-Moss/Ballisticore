import api from './client'

export const getAmmunitionTypes = (includeInactive = false) =>
  api.get('/api/ammunition-types/', { params: { include_inactive: includeInactive } })

export const getAmmunitionType = (id) => api.get(`/api/ammunition-types/${id}`)
export const createAmmunitionType = (data) => api.post('/api/ammunition-types/', data)
export const updateAmmunitionType = (id, data) => api.put(`/api/ammunition-types/${id}`, data)
export const deleteAmmunitionType = (id) => api.delete(`/api/ammunition-types/${id}`)
