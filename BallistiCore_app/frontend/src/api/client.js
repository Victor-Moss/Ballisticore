import axios from 'axios'

// Same-origin by default: requests go to `/api/...` on whatever host served the
// page (localhost, a LAN IP, or an ngrok URL). In dev the Vite proxy forwards
// these to the backend; in production Nginx does. Override with VITE_API_URL only
// if you really need to point at a different backend host.
// A generous global timeout is a backstop so no request can hang forever if the
// server accepts the connection but never responds. It's deliberately long so it
// doesn't cut off legitimate slow operations (data export/import, PDF/report
// downloads). Fast interactive calls (e.g. login) set a tighter per-request
// timeout of their own.
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '', timeout: 60000 })

// Attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bc_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401 — an expired/invalid session on a normal page: clear the token and
// bounce to the login screen. But do NOT redirect when already on /login: there
// a 401 just means wrong credentials, and reloading would wipe the error message
// the login form is about to show. Always reject so callers can handle it.
api.interceptors.response.use(
  (r) => r,
  (err) => {
    const onLoginPage = window.location.pathname === '/login'
    if (err.response?.status === 401 && !onLoginPage) {
      localStorage.removeItem('bc_token')
      localStorage.removeItem('bc_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
