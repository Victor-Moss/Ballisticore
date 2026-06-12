import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useBranding } from '../context/BrandingContext'
import { useLicense } from '../context/LicenseContext'
import { useTheme } from '../context/ThemeContext'
import { hasPerm, canAccessAdmin } from '../utils/permissions'
import Logo from './Logo'
import {
  LayoutDashboard, ClipboardList, Crosshair, Undo2, History,
  FileText, Shield, Archive, Settings, LogOut, Sun, Moon, Menu, X,
} from 'lucide-react'

function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const dark = theme === 'dark'
  return (
    <button
      onClick={toggle}
      title={dark ? 'Switch to light theme' : 'Switch to dark theme'}
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
      className="grid place-items-center h-9 w-9 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
    >
      {dark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  )
}

// `perm` mirrors the route guards in App.jsx and the backend permission rules.
// No `perm` → always visible (Dashboard). `admin: true` → use canAccessAdmin.
const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { to: '/register', label: 'Register', icon: ClipboardList, perm: 'perm_access_database' },
  { to: '/issue', label: 'Issue Firearm', icon: Crosshair, perm: 'perm_new_permits' },
  { to: '/return', label: 'Return Firearm', icon: Undo2, perm: 'perm_return_permits' },
  { to: '/history', label: 'History', icon: History, perm: 'perm_view_register_history' },
  { to: '/permits', label: 'Permits', icon: FileText, perm: ['perm_new_permits', 'perm_send_whatsapp'] },
  { to: '/guards', label: 'Guards', icon: Shield, perm: 'perm_manage_staff' },
  { to: '/firearms', label: 'Firearms', icon: Archive, perm: 'perm_manage_weapons' },
  { to: '/admin', label: 'Admin', icon: Settings, admin: true },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { app_name, company_name } = useBranding()
  const { read_only, state: licenseState, message: licenseMessage } = useLicense()
  // Off-canvas sidebar state — only relevant below the `md` breakpoint (768px).
  // At `md` and up the sidebar is always visible and this is ignored.
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const visibleItems = navItems
    .filter((item) => (item.admin ? canAccessAdmin(user) : hasPerm(user, item.perm)))
    // In read-only mode, hide the firearm-movement actions (Issue/Return) — the
    // server rejects them anyway. Viewing routes stay available.
    .filter((item) => !(read_only && (item.to === '/issue' || item.to === '/return')))

  const initials = (user?.username || '?').slice(0, 2).toUpperCase()

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Backdrop — only rendered on mobile when the drawer is open */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar — off-canvas drawer below md (768px), static column at md+ */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 shrink-0 bg-slate-950/80 border-r border-slate-800 backdrop-blur-xl flex flex-col transition-transform duration-200 md:static md:z-auto md:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="px-5 py-5 flex items-center gap-3 border-b border-slate-800/80">
          <Logo size={40} />
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-bold text-white tracking-tight leading-tight truncate">{app_name}</h1>
            <p className="text-xs text-slate-400 truncate">{company_name}</p>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            aria-label="Close menu"
            className="md:hidden grid place-items-center h-8 w-8 shrink-0 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-1">
          {visibleItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.exact}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  `group relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-blue-600/15 text-white'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={`absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 rounded-r-full bg-blue-500 transition-opacity ${
                        isActive ? 'opacity-100' : 'opacity-0'
                      }`}
                    />
                    <Icon
                      size={18}
                      className={isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-300'}
                    />
                    {item.label}
                  </>
                )}
              </NavLink>
            )
          })}
        </nav>

        <div className="px-3 py-4 border-t border-slate-800/80">
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="grid place-items-center h-9 w-9 shrink-0 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 ring-1 ring-white/10 text-xs font-bold text-slate-200">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-200 truncate">{user?.username}</p>
              <p className="text-xs text-slate-500">{user?.is_admin ? 'Administrator' : 'Operator'}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="grid place-items-center h-8 w-8 rounded-lg text-slate-500 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top navigation bar */}
        <header className="h-12 shrink-0 flex items-center gap-1 px-4 border-b border-slate-800/60">
          <button
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
            className="md:hidden grid place-items-center h-9 w-9 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
          >
            <Menu size={18} />
          </button>
          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
          </div>
        </header>
        {/* License banner — red & persistent in read-only (expired/invalid),
            amber as expiry approaches. */}
        {(read_only || licenseState === 'warning') && licenseMessage && (
          <div className={`shrink-0 px-4 py-2 text-sm font-medium text-center ${
            read_only ? 'bg-red-600 text-white' : 'bg-amber-500 text-amber-950'
          }`}>
            {licenseMessage}
          </div>
        )}
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
