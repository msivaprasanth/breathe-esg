import { createContext, useContext, useState, useEffect } from 'react'
import { auth as authApi } from '../api/endpoints'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [tenant, setTenant] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const saved = localStorage.getItem('user')
    const savedTenant = localStorage.getItem('tenant')
    if (token && saved) {
      setUser(JSON.parse(saved))
      if (savedTenant) setTenant(JSON.parse(savedTenant))
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const { data } = await authApi.login(username, password)
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    if (data.tenant) localStorage.setItem('tenant', JSON.stringify(data.tenant))
    setUser(data.user)
    setTenant(data.tenant)
    return data
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('tenant')
    setUser(null)
    setTenant(null)
  }

  return (
    <AuthContext.Provider value={{ user, tenant, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)