import api from './client'

export const getNetworkInfo = () => api.get('/api/network/info')
