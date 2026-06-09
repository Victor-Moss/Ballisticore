import api from './client'

export const getBrandingFull = () => api.get('/api/branding/full')
export const updateBranding  = (data) => api.put('/api/branding/', data)
