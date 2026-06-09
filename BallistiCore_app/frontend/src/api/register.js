import api from './client'

export const getCurrentRegister = () => api.get('/api/register/')
export const getRegisterForGuard = (guardId) => api.get(`/api/register/guard/${guardId}`)
export const issueFirearm = (data) => api.post('/api/register/issue', data)
export const returnFirearm = (data) => api.post('/api/register/return', data)
export const getHistory = (params = {}) => api.get('/api/register/history', { params })
export const getHistoryForGuard = (guardId) => api.get(`/api/register/history/guard/${guardId}`)
export const getHistoryForFirearm = (firearmId) => api.get(`/api/register/history/firearm/${firearmId}`)
