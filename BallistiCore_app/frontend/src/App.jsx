import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { BrandingProvider, useBranding } from './context/BrandingContext'
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

function FullScreenLoader() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <p className="text-sm text-slate-500">Loading…</p>
    </div>
  )
}

function ProtectedRoute({ children }) {
  const { user } = useAuth()
  const { setup_completed, loaded } = useBranding()
  if (!user) return <Navigate to="/login" replace />
  if (!loaded) return <FullScreenLoader />
  // First run after install: send admins through the setup wizard.
  if (!setup_completed && user.is_admin) return <Navigate to="/setup" replace />
  return <Layout>{children}</Layout>
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
      <Route path="/register" element={<ProtectedRoute><Register /></ProtectedRoute>} />
      <Route path="/issue" element={<ProtectedRoute><IssueFirearm /></ProtectedRoute>} />
      <Route path="/return" element={<ProtectedRoute><ReturnFirearm /></ProtectedRoute>} />
      <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
      <Route path="/permits" element={<ProtectedRoute><Permits /></ProtectedRoute>} />
      <Route path="/guards" element={<ProtectedRoute><Guards /></ProtectedRoute>} />
      <Route path="/guards/:id" element={<ProtectedRoute><GuardDetail /></ProtectedRoute>} />
      <Route path="/firearms" element={<ProtectedRoute><Firearms /></ProtectedRoute>} />
      <Route path="/firearms/:id" element={<ProtectedRoute><FirearmDetail /></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute><Admin /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <BrandingProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrandingProvider>
    </BrowserRouter>
  )
}
