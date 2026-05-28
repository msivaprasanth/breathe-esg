import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Leaf, AlertCircle } from 'lucide-react'
import Spinner from '../components/Spinner'
import './Login.css'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async e => {
    e.preventDefault()
    if (!username || !password) return
    setLoading(true); setError('')
    try {
      await login(username, password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid credentials. Try analyst1 / analyst123')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-root">
      <div className="login-bg-grid" />
      <div className="login-card fade-in">
        <div className="login-brand">
          <div className="login-logo-mark">
            <Leaf size={20} strokeWidth={2} />
          </div>
          <div>
            <div className="login-brand-name">Breathe ESG</div>
            <div className="login-brand-sub">Emissions Data Platform</div>
          </div>
        </div>

        <div className="login-divider" />

        <h1 className="login-title">Sign in</h1>
        <p className="login-desc">Access your emissions review workspace.</p>

        {error && (
          <div className="login-error">
            <AlertCircle size={13} />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="field-group">
            <label className="field-label">Username</label>
            <input
              className="field-input"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoFocus autoComplete="username"
              placeholder="analyst1"
            />
          </div>
          <div className="field-group">
            <label className="field-label">Password</label>
            <input
              className="field-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              placeholder="••••••••"
            />
          </div>
          <button className="login-btn" type="submit" disabled={loading}>
            {loading ? <Spinner size={14} /> : 'Sign in'}
          </button>
        </form>

        <div className="login-hint">
          <span>Demo credentials</span>
          <code>analyst1 / analyst123</code>
        </div>
      </div>
    </div>
  )
}