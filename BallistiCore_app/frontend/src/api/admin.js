import api from './client'

// Gracefully stop the server. Super admin only (enforced on the backend).
export const shutdownServer = () => api.post('/api/admin/shutdown')
