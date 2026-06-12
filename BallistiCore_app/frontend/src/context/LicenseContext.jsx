import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getLicense } from '../api/license'

// Permissive defaults: if the license endpoint can't be reached we do NOT trap
// the UI in read-only mode — the backend middleware is the hard gate, so a
// momentary fetch failure can't let a mutation through anyway.
const DEFAULTS = {
  state: 'active',
  read_only: false,
  message: '',
  company: null,
  expires_at: null,
  days_left: null,
}

const LicenseContext = createContext({ ...DEFAULTS, loaded: false, refresh: () => {} })

export function LicenseProvider({ children }) {
  const [license, setLicense] = useState(DEFAULTS)
  const [loaded, setLoaded] = useState(false)

  const refresh = useCallback(() => {
    return getLicense()
      .then((res) => setLicense({ ...DEFAULTS, ...res.data }))
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

  useEffect(() => { refresh() }, [refresh])

  return (
    <LicenseContext.Provider value={{ ...license, loaded, refresh }}>
      {children}
    </LicenseContext.Provider>
  )
}

export function useLicense() {
  return useContext(LicenseContext)
}
