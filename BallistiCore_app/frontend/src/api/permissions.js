import api from './client'

export const getPermissionsForGuard = (guardId) => api.get(`/api/permissions/guard/${guardId}`)
export const setPermission = (data) => api.post('/api/permissions/', data)
export const deletePermission = (id) => api.delete(`/api/permissions/${id}`)
