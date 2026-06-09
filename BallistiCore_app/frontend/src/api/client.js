import axios from 'axios'

// Same-origin by default: requests go to `/api/...` on whatever host served the
// page (localhost, a LAN IP, or an ngrok URL). In dev the Vite proxy forwards
// these to the backend; in production Nginx does. Override with VITE_API_URL only
// if you really need to point at a different backend host.
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '' })

// Attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bc_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401 — clear token and redirect to login
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('bc_token')
      localStorage.removeItem('bc_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
