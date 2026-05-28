import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

import {
  LayoutDashboard,
  Upload,
  ClipboardList,
  LogOut,
  Leaf,
  ChevronRight
} from 'lucide-react'

import './Layout.css'

const NAV = [
  {
    to: '/',
    icon: LayoutDashboard,
    label: 'Dashboard'
  },
  {
    to: '/upload',
    icon: Upload,
    label: 'Ingest Data'
  },
  {
    to: '/review',
    icon: ClipboardList,
    label: 'Review Queue'
  },
]

export default function Layout({ children }) {

  const {
    user,
    tenant,
    logout
  } = useAuth()

  const navigate = useNavigate()

  const handleLogout = () => {

    logout()

    navigate('/login')
  }

  return (
    <div className="layout">

      <aside className="sidebar">

        <div className="sidebar-logo">

          <div className="logo-mark">
            <Leaf size={16} strokeWidth={2.5} />
          </div>

          <div className="logo-text">
            <span className="logo-name">
              Breathe
            </span>

            <span className="logo-tag">
              ESG
            </span>
          </div>

        </div>

        <div className="sidebar-tenant">

          <div className="tenant-dot" />

          <div className="tenant-info">

            <span className="tenant-name">
              {tenant?.name || '—'}
            </span>

            <span className="tenant-role">
              {tenant?.role || 'analyst'}
            </span>

          </div>

        </div>

        <nav className="sidebar-nav">

          <div className="nav-label">
            WORKSPACE
          </div>

          {NAV.map(({
            to,
            icon: Icon,
            label
          }) => (

            <NavLink
              key={to}
              to={to}
              end
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''}`
              }
            >

              <Icon
                size={15}
                strokeWidth={1.8}
              />

              <span>{label}</span>

              <ChevronRight
                size={11}
                className="nav-arrow"
              />

            </NavLink>
          ))}

        </nav>

        <div className="sidebar-footer">

          <div className="user-info">

            <div className="user-avatar">
              {
                (
                  (user?.first_name?.[0] || '') +
                  (user?.last_name?.[0] || '')
                ) || 'U'
              }
            </div>

            <div className="user-details">

              <span className="user-name">
                {
                  user?.first_name || user?.username
                }
              </span>

              <span className="user-email">
                {user?.email || '—'}
              </span>

            </div>

          </div>

          <button
            className="logout-btn"
            onClick={handleLogout}
            title="Sign out"
          >
            <LogOut
              size={14}
              strokeWidth={1.8}
            />
          </button>

        </div>

      </aside>

      <main className="main-content">

        <div className="content-inner fade-in">
          {children}
        </div>

      </main>

    </div>
  )
}