import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useBranding } from '../context/BrandingContext'
import Logo from './Logo'
import {
  LayoutDashboard, ClipboardList, Crosshair, Undo2, History,
  FileText, Shield, Archive, Settings, LogOut,
} from 'lucide-react'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { to: '/register', label: 'Register', icon: ClipboardList },
  { to: '/issue', label: 'Issue Firearm', icon: Crosshair },
  { to: '/return', label: 'Return Firearm', icon: Undo2 },
  { to: '/history', label: 'History', icon: History },
  { to: '/permits', label: 'Permits', icon: FileText },
  { to: '/guards', label: 'Guards', icon: Shield },
  { to: '/firearms', label: 'Firearms', icon: Archive },
  { to: '/admin', label: 'Admin', icon: Settings, adminOnly: true },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { app_name, company_name } = useBranding()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const visibleItems = navItems.filter(
    (item) => !item.adminOnly || user?.is_admin
  )

  const initials = (user?.username || '?').slice(0, 2).toUpperCase()

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 bg-slate-950/80 border-r border-slate-800 backdrop-blur-xl flex flex-col">
        <div className="px-5 py-5 flex items-center gap-3 border-b border-slate-800/80">
          <Logo size={40} />
          <div className="min-w-0">
            <h1 className="text-base font-bold text-white tracking-tight leading-tight truncate">{app_name}</h1>
            <p className="text-xs text-slate-400 truncate">{company_name}</p>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-1">
          {visibleItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.exact}
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
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
