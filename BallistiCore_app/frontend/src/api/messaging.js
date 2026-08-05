import api from './client'

// Active provider only (no credentials) — used by guard forms to show the right
// delivery field. Available to any signed-in user.
export const getMessagingProvider = () => api.get('/api/messaging/provider')

// Full config incl. credentials — admin only (Setup Wizard / Settings form).
export const getMessagingConfig = () => api.get('/api/messaging/')
export const updateMessagingConfig = (data) => api.put('/api/messaging/', data)
export const testMessaging = (data) => api.post('/api/messaging/test', data)
