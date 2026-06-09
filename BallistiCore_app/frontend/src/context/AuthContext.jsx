import { createContext, useContext, useState, useCallback } from 'react'
import { login as apiLogin, getMe } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('bc_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  const login = useCallback(async (username, password) => {
    const res = await apiLogin(username, password)
    const { access_token } = res.data
    localStorage.setItem('bc_token', access_token)
    const meRes = await getMe()
    const userData = meRes.data
    localStorage.setItem('bc_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('bc_token')
    localStorage.removeItem('bc_user')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
