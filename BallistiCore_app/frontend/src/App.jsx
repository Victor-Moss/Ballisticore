import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { BrandingProvider, useBranding } from './context/BrandingContext'
import { LicenseProvider } from './context/LicenseContext'
import { ThemeProvider } from './context/ThemeContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import SetupWizard from './pages/SetupWizard'
import Dashboard from './pages/Dashboard'
import Guards from './pages/Guards'
import GuardDetail from './pages/GuardDetail'
import Firearms from './pages/Firearms'
import FirearmDetail from './pages/FirearmDetail'
import Register from './pages/Register'
import IssueFirearm from './pages/IssueFirearm'
import ReturnFirearm from './pages/ReturnFirearm'
import History from './pages/History'
import Permits from './pages/Permits'
import Admin from './pages/Admin'
import AccessDenied from './components/AccessDenied'
import { hasPerm, canAccessAdmin } from './utils/permissions'

function FullScreenLoader() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <p className="text-sm text-slate-500">Loading…</p>
    </div>
  )
}

function ProtectedRoute({ children, perm }) {
  const { user } = useAuth()
  const { setup_completed, loaded } = useBranding()
  if (!user) return <Navigate to="/login" replace />
  if (!loaded) return <FullScreenLoader />
  // First run after install: send admins through the setup wizard.
  if (!setup_completed && user.is_admin) return <Navigate to="/setup" replace />
  // Per-route permission gate. `perm` may be a key, an array of keys, or a
  // predicate function (user) => boolean. Missing → render Access Denied
  // inside the normal Layout so the user keeps their navigation.
  const allowed =
    !perm || (typeof perm === 'function' ? perm(user) : hasPerm(user, perm))
  return <Layout>{allowed ? children : <AccessDenied />}</Layout>
}

// Full-screen setup wizard — rendered without the app Layout/sidebar.
function SetupRoute({ children }) {
  const { user } = useAuth()
  const { setup_completed, loaded } = useBranding()
  if (!user) return <Navigate to="/login" replace />
  if (!loaded) return <FullScreenLoader />
  if (setup_completed) return <Navigate to="/" replace />
  return children
}

function PublicRoute({ children }) {
  const { user } = useAuth()
  if (user) return <Navigate to="/" replace />
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/setup" element={<SetupRoute><SetupWizard /></SetupRoute>} />
      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/register" element={<ProtectedRoute perm="perm_access_database"><Register /></ProtectedRoute>} />
      <Route path="/issue" element={<ProtectedRoute perm="perm_new_permits"><IssueFirearm /></ProtectedRoute>} />
      <Route path="/return" element={<ProtectedRoute perm="perm_return_permits"><ReturnFirearm /></ProtectedRoute>} />
      <Route path="/history" element={<ProtectedRoute perm="perm_view_register_history"><History /></ProtectedRoute>} />
      <Route path="/permits" element={<ProtectedRoute perm={['perm_new_permits', 'perm_send_whatsapp']}><Permits /></ProtectedRoute>} />
      <Route path="/guards" element={<ProtectedRoute perm="perm_manage_staff"><Guards /></ProtectedRoute>} />
      <Route path="/guards/:id" element={<ProtectedRoute perm="perm_manage_staff"><GuardDetail /></ProtectedRoute>} />
      <Route path="/firearms" element={<ProtectedRoute perm="perm_manage_weapons"><Firearms /></ProtectedRoute>} />
      <Route path="/firearms/:id" element={<ProtectedRoute perm="perm_manage_weapons"><FirearmDetail /></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute perm={canAccessAdmin}><Admin /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <BrandingProvider>
          <LicenseProvider>
            <AuthProvider>
              <AppRoutes />
            </AuthProvider>
          </LicenseProvider>
        </BrandingProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}
