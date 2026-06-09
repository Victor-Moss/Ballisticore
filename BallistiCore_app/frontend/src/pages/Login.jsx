import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useBranding } from '../context/BrandingContext'
import Logo from '../components/Logo'
import { User, Lock, AlertCircle, Loader2 } from 'lucide-react'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const { app_name, company_name } = useBranding()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/')
    } catch (err) {
      if (err.response) {
        setError(err.response.data?.detail || 'Invalid credentials')
      } else {
        setError('Cannot reach the server. Check your connection and try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Brand */}
        <div className="flex flex-col items-center mb-8">
          <Logo size={64} />
          <h1 className="mt-4 text-2xl font-bold text-white tracking-tight">{app_name}</h1>
          <p className="text-sm text-slate-400">{company_name}</p>
        </div>

        {/* Card */}
        <div className="bc-card p-7">
          <h2 className="text-base font-semibold text-white mb-1">Sign in</h2>
          <p className="text-xs text-slate-400 mb-6">Enter your credentials to access the register.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="bc-label">Username</label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="bc-input pl-9"
                  required
                  autoFocus
                  placeholder="admin"
                />
              </div>
            </div>

            <div>
              <label className="bc-label">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bc-input pl-9"
                  required
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-2 text-sm text-red-300 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button type="submit" disabled={loading} className="bc-btn-primary w-full flex items-center justify-center gap-2">
              {loading && <Loader2 size={16} className="animate-spin" />}
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          {app_name} · Firearms Register Management
        </p>
      </div>
    </div>
  )
}
