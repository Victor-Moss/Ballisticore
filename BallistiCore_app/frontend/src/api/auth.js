import api from './client'

// The login flow uses a short timeout so a stalled/unresponsive server surfaces
// a clear error within a few seconds instead of spinning forever. These are
// quick endpoints, so 5s is ample.
const AUTH_TIMEOUT = 5000

export const login = (username, password) => {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  return api.post('/api/auth/login', form, { timeout: AUTH_TIMEOUT })
}

export const getMe = () => api.get('/api/auth/me', { timeout: AUTH_TIMEOUT })
export const getUsers = () => api.get('/api/auth/users')
export const createUser = (data) => api.post('/api/auth/users', data)
export const updateUser = (id, data) => api.put(`/api/auth/users/${id}`, data)
export const deactivateUser = (id) => api.put(`/api/auth/users/${id}/deactivate`)
export const reactivateUser = (id) => api.put(`/api/auth/users/${id}/reactivate`)
