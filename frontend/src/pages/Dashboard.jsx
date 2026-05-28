import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { dashboard as dashApi } from '../api/endpoints'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import { Activity, CheckCircle, AlertTriangle, Clock, XCircle, Upload, ArrowRight, Database } from 'lucide-react'
import './Dashboard.css'

function StatCard({ label, value, icon: Icon, color, sub, link }) {
  const card = (
    <div className="stat-card" style={{ '--card-color': color }}>
      <div className="stat-icon"><Icon size={16} strokeWidth={1.8} /></div>
      <div className="stat-body">
        <div className="stat-value">{value ?? <div className="skeleton" style={{width:40,height:24}} />}</div>
        <div className="stat-label">{label}</div>
        {sub && <div className="stat-sub">{sub}</div>}
      </div>
      {link && <ArrowRight size={13} className="stat-arrow" />}
    </div>
  )
  return link ? <Link to={link} style={{ textDecoration: 'none' }}>{card}</Link> : card
}

function ScopeBar({ data }) {
  if (!data) return null
  const scopes = Object.entries(data)
  return (
    <div className="scope-grid">
      {scopes.map(([name, counts]) => (
        <div key={name} className="scope-card">
          <div className="scope-header">
            <span className={`scope-pill s${name.slice(-1)}`}>{name}</span>
            <span className="scope-total">{counts.total} rows</span>
          </div>
          <div className="scope-bar-track">
            {counts.approved > 0 && (
              <div className="scope-bar-seg approved" style={{ width: `${counts.approved / counts.total * 100}%` }} title={`Approved: ${counts.approved}`} />
            )}
            {counts.pending > 0 && (
              <div className="scope-bar-seg pending" style={{ width: `${counts.pending / counts.total * 100}%` }} title={`Pending: ${counts.pending}`} />
            )}
            {counts.flagged > 0 && (
              <div className="scope-bar-seg flagged" style={{ width: `${counts.flagged / counts.total * 100}%` }} title={`Flagged: ${counts.flagged}`} />
            )}
            {counts.rejected > 0 && (
              <div className="scope-bar-seg rejected" style={{ width: `${counts.rejected / counts.total * 100}%` }} title={`Rejected: ${counts.rejected}`} />
            )}
          </div>
          <div className="scope-legend">
            {['approved','pending','flagged','rejected'].map(s => counts[s] > 0 && (
              <span key={s} className={`legend-item ${s}`}>{counts[s]} {s}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    dashApi.metrics().then(r => setMetrics(r.data)).finally(() => setLoading(false))
  }, [])

  const sourceLabels = {
    SAP_FUEL_PROCUREMENT: 'SAP Fuel & Procurement',
    UTILITY_ELECTRICITY: 'Utility Electricity',
    CORPORATE_TRAVEL: 'Corporate Travel',
  }

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300 }}>
      <Spinner size={28} />
    </div>
  )

  return (
    <div className="dashboard fade-in">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
          <div>
            <h1 className="page-title">Dashboard</h1>
            <p className="page-subtitle">Emissions data ingestion overview — review status at a glance.</p>
          </div>
          <Link to="/upload" className="upload-cta">
            <Upload size={13} /> Ingest Data
          </Link>
        </div>
      </div>

      {/* Stat cards */}
      <div className="stats-grid">
        <StatCard label="Total Records" value={metrics?.total} icon={Database} color="var(--text-secondary)" />
        <StatCard label="Pending Review" value={metrics?.pending} icon={Clock} color="var(--amber)" link="/review?status=PENDING" />
        <StatCard label="Flagged" value={metrics?.flagged} icon={AlertTriangle} color="var(--red)" link="/review?status=FLAGGED" />
        <StatCard label="Approved" value={metrics?.approved} icon={CheckCircle} color="var(--green)" link="/review?status=APPROVED" />
        <StatCard label="Rejected" value={metrics?.rejected} icon={XCircle} color="var(--text-muted)" link="/review?status=REJECTED" />
        <StatCard label="Total Batches" value={metrics?.total_batches} icon={Activity} color="var(--blue)"
          sub={metrics?.failed_batches > 0 ? `${metrics.failed_batches} failed` : null}
        />
      </div>

      <div className="dash-grid">
        {/* Scope breakdown */}
        <div className="dash-panel">
          <div className="panel-header">
            <span className="panel-title">Scope Breakdown</span>
            <Link to="/review" className="panel-link">View all <ArrowRight size={11} /></Link>
          </div>
          <ScopeBar data={metrics?.scope_breakdown} />
        </div>

        {/* Source breakdown */}
        <div className="dash-panel">
          <div className="panel-header">
            <span className="panel-title">By Data Source</span>
          </div>
          <div className="source-list">
            {Object.entries(metrics?.source_breakdown || {}).map(([src, counts]) => (
              <div key={src} className="source-row">
                <div className="source-name">{sourceLabels[src] || src}</div>
                <div className="source-counts">
                  {counts.pending > 0 && <span className="src-count pending">{counts.pending} pending</span>}
                  {counts.flagged > 0 && <span className="src-count flagged">{counts.flagged} flagged</span>}
                  {counts.approved > 0 && <span className="src-count approved">{counts.approved} approved</span>}
                </div>
                <div className="source-total">{counts.total}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent batches */}
        <div className="dash-panel wide">
          <div className="panel-header">
            <span className="panel-title">Recent Ingestion Batches</span>
            <Link to="/upload" className="panel-link">Upload new <ArrowRight size={11} /></Link>
          </div>
          <table className="batch-table">
            <thead>
              <tr>
                <th>File</th><th>Source</th><th>Rows</th><th>Flagged</th><th>Failed</th><th>Status</th><th>When</th>
              </tr>
            </thead>
            <tbody>
              {metrics?.recent_batches?.map(b => (
                <tr key={b.id}>
                  <td className="mono truncate" title={b.original_filename}>{b.original_filename}</td>
                  <td>{sourceLabels[b.source_type] || b.source_type}</td>
                  <td className="mono">{b.parsed_rows}</td>
                  <td className="mono" style={{ color: b.flagged_rows > 0 ? 'var(--red)' : 'var(--text-muted)' }}>{b.flagged_rows}</td>
                  <td className="mono" style={{ color: b.failed_rows > 0 ? 'var(--red)' : 'var(--text-muted)' }}>{b.failed_rows}</td>
                  <td><StatusBadge status={b.status} /></td>
                  <td className="mono muted">{new Date(b.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}