import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { BrandingProvider } from './context/BrandingContext'
import Layout from './components/Layout'
import Login from './pages/Login'
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

function ProtectedRoute({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
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
