import api from './client'

export const getGuards = (includeInactive = false) =>
  api.get('/api/guards/', { params: { include_inactive: includeInactive } })

export const getGuard = (id) => api.get(`/api/guards/${id}`)
export const getGuardPermissions = (id) => api.get(`/api/guards/${id}/permissions`)
export const createGuard = (data) => api.post('/api/guards/', data)
export const updateGuard = (id, data) => api.put(`/api/guards/${id}`, data)
export const deactivateGuard = (id) => api.put(`/api/guards/${id}/deactivate`)
export const reactivateGuard = (id) => api.put(`/api/guards/${id}/reactivate`)
export const deleteGuard = (id) => api.delete(`/api/guards/${id}`)

// Sign-in account (operator-managed)
export const setGuardAccount = (id, data) => api.post(`/api/guards/${id}/account`, data)
export const resetGuardPassword = (id) => api.put(`/api/guards/${id}/account/reset-password`)
export const deleteGuardAccount = (id) => api.delete(`/api/guards/${id}/account`)

// Guard self-service (public — used from the issue screen when a guard forgot their password)
export const guardRequestReset = (username) =>
  api.post('/api/guard-account/request-reset', { username })
export const guardResetPassword = (username, otp, newPassword) =>
  api.post('/api/guard-account/reset-password', { username, otp, new_password: newPassword })
