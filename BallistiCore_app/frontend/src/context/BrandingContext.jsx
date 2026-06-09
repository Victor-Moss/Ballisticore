import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import api from '../api/client'

const DEFAULTS = {
  app_name: 'BallistiCore',
  company_name: 'Your Company',
  permit_prefix: 'BC',
  primary_color: '#1d4ed8',
}

const BrandingContext = createContext({ ...DEFAULTS, refresh: () => {} })

export function BrandingProvider({ children }) {
  const [branding, setBranding] = useState(DEFAULTS)

  const apply = (data) => {
    const merged = { ...DEFAULTS, ...data }
    setBranding(merged)
    document.documentElement.style.setProperty('--color-primary', merged.primary_color)
    document.title = merged.app_name
  }

  const refresh = useCallback(() => {
    return api.get('/api/branding/').then((res) => apply(res.data)).catch(() => {})
  }, [])

  useEffect(() => { refresh() }, [refresh])

  return (
    <BrandingContext.Provider value={{ ...branding, refresh }}>
      {children}
    </BrandingContext.Provider>
  )
}

export function useBranding() {
  return useContext(BrandingContext)
}
