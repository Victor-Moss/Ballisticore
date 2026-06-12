import api from './client'

export const getLicense = () => api.get('/api/license/')
