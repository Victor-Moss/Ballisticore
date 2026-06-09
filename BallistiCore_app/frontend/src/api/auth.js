import api from './client'

export const login = (username, password) => {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  return api.post('/api/auth/login', form)
}

export const getMe = () => api.get('/api/auth/me')
export const getUsers = () => api.get('/api/auth/users')
export const createUser = (data) => api.post('/api/auth/users', data)
export const updateUser = (id, data) => api.put(`/api/auth/users/${id}`, data)
export const deactivateUser = (id) => api.put(`/api/auth/users/${id}/deactivate`)
export const reactivateUser = (id) => api.put(`/api/auth/users/${id}/reactivate`)
