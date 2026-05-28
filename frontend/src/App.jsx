import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import ReviewQueue from './pages/ReviewQueue'
import RecordDetail from './pages/RecordDetail'
import Spinner from './components/Spinner'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <Spinner size={28} />
    </div>
  )
  if (!user) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
      <Route path="/review" element={<ProtectedRoute><ReviewQueue /></ProtectedRoute>} />
      <Route path="/review/:id" element={<ProtectedRoute><RecordDetail /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: 'var(--bg-elevated)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-accent)',
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
            },
            success: { iconTheme: { primary: 'var(--green)', secondary: 'var(--bg-elevated)' } },
            error:   { iconTheme: { primary: 'var(--red)',   secondary: 'var(--bg-elevated)' } },
          }}
        />
      </BrowserRouter>
    </AuthProvider>
  )
}