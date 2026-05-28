import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { review as reviewApi, actions } from '../api/endpoints'
import StatusBadge from '../components/StatusBadge'
import ScopeBadge from '../components/ScopeBadge'
import Spinner from '../components/Spinner'
import { CheckCircle, XCircle, ChevronRight, AlertTriangle, Search, Filter, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import './ReviewQueue.css'

const SOURCE_LABELS = {
  SAP_FUEL_PROCUREMENT: 'SAP',
  UTILITY_ELECTRICITY: 'Utility',
  CORPORATE_TRAVEL: 'Travel',
}

const CAT_LABELS = {
  MOBILE_COMBUSTION: 'Mobile Combustion',
  STATIONARY_COMBUSTION: 'Stationary Combustion',
  PURCHASED_ELECTRICITY: 'Electricity',
  PURCHASED_GOODS: 'Procurement',
  BUSINESS_TRAVEL_AIR: 'Flight',
  BUSINESS_TRAVEL_HOTEL: 'Hotel',
  BUSINESS_TRAVEL_GROUND: 'Ground Travel',
}

export default function ReviewQueue() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [records, setRecords] = useState([])
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(new Set())
  const [actionLoading, setActionLoading] = useState(false)
  const [rejectNote, setRejectNote] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [page, setPage] = useState(1)

  const statusFilter = searchParams.get('status') || ''
  const scopeFilter = searchParams.get('scope') || ''
  const sourceFilter = searchParams.get('source') || ''
  const search = searchParams.get('search') || ''

  const fetchRecords = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, page_size: 50 }
      if (statusFilter) params.status = statusFilter
      if (scopeFilter) params.scope = scopeFilter
      if (sourceFilter) params.source = sourceFilter
      if (search) params.search = search
      const { data } = await reviewApi.list(params)
      setRecords(data.results)
      setCount(data.count)
    } finally { setLoading(false) }
  }, [statusFilter, scopeFilter, sourceFilter, search, page])

  useEffect(() => { fetchRecords() }, [fetchRecords])

  const setFilter = (key, val) => {
    const p = new URLSearchParams(searchParams)
    if (val) p.set(key, val); else p.delete(key)
    p.delete('page')
    setSearchParams(p)
    setPage(1); setSelected(new Set())
  }

  const toggleSelect = id => {
    const s = new Set(selected)
    s.has(id) ? s.delete(id) : s.add(id)
    setSelected(s)
  }

  const toggleAll = () => {
    if (selected.size === records.length) setSelected(new Set())
    else setSelected(new Set(records.map(r => r.id)))
  }

  const handleApprove = async () => {
    if (!selected.size) return
    setActionLoading(true)
    try {
      const { data } = await actions.approve([...selected])
      toast.success(`Approved ${data.approved} record${data.approved !== 1 ? 's' : ''}`)
      setSelected(new Set()); fetchRecords()
    } catch { toast.error('Approval failed') }
    finally { setActionLoading(false) }
  }

  const handleReject = async () => {
    if (!rejectNote.trim()) return
    setActionLoading(true)
    try {
      const { data } = await actions.reject([...selected], rejectNote)
      toast.success(`Rejected ${data.rejected} record${data.rejected !== 1 ? 's' : ''}`)
      setSelected(new Set()); setShowRejectModal(false); setRejectNote(''); fetchRecords()
    } catch { toast.error('Rejection failed') }
    finally { setActionLoading(false) }
  }

  const formatQty = (qty, unit) => {
    const n = parseFloat(qty)
    if (isNaN(n)) return '—'
    const formatted = n >= 1000 ? n.toLocaleString(undefined, { maximumFractionDigits: 1 }) : n.toFixed(2)
    return `${formatted} ${unit}`
  }

  return (
    <div className="review-page fade-in">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
          <div>
            <h1 className="page-title">Review Queue</h1>
            <p className="page-subtitle">{count} records — select rows to approve or reject in bulk.</p>
          </div>
          <button className="icon-btn" onClick={fetchRecords} title="Refresh">
            <RefreshCw size={14} strokeWidth={1.8} />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        <div className="filter-group">
          <Filter size={12} style={{ color: 'var(--text-muted)' }} />
          {['', 'PENDING', 'FLAGGED', 'APPROVED', 'REJECTED'].map(s => (
            <button key={s} className={`filter-pill ${statusFilter === s ? 'active' : ''}`}
              onClick={() => setFilter('status', s)}>
              {s || 'All'}
            </button>
          ))}
        </div>
        <div className="filter-group">
          {['', '1', '2', '3'].map(s => (
            <button key={s} className={`filter-pill ${scopeFilter === s ? 'active scope' : ''}`}
              onClick={() => setFilter('scope', s)}>
              {s ? `Scope ${s}` : 'All Scopes'}
            </button>
          ))}
        </div>
        <div className="filter-group">
          {['', 'SAP_FUEL_PROCUREMENT', 'UTILITY_ELECTRICITY', 'CORPORATE_TRAVEL'].map(s => (
            <button key={s} className={`filter-pill ${sourceFilter === s ? 'active' : ''}`}
              onClick={() => setFilter('source', s)}>
              {s ? SOURCE_LABELS[s] : 'All Sources'}
            </button>
          ))}
        </div>
        <div className="search-wrap">
          <Search size={12} />
          <input className="search-input" placeholder="Search metadata…"
            defaultValue={search}
            onChange={e => setFilter('search', e.target.value)} />
        </div>
      </div>

      {/* Bulk action bar */}
      {selected.size > 0 && (
        <div className="bulk-bar slide-in">
          <span className="bulk-count">{selected.size} selected</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="bulk-btn approve" onClick={handleApprove} disabled={actionLoading}>
              {actionLoading ? <Spinner size={12} /> : <CheckCircle size={13} />}
              Approve
            </button>
            <button className="bulk-btn reject" onClick={() => setShowRejectModal(true)} disabled={actionLoading}>
              <XCircle size={13} /> Reject
            </button>
          </div>
          <button className="bulk-clear" onClick={() => setSelected(new Set())}>Clear</button>
        </div>
      )}

      {/* Table */}
      <div className="review-table-wrap">
        {loading ? (
          <div className="table-loading"><Spinner size={24} /></div>
        ) : records.length === 0 ? (
          <div className="table-empty">No records match these filters.</div>
        ) : (
          <table className="review-table">
            <thead>
              <tr>
                <th>
                  <input type="checkbox" className="cb"
                    checked={selected.size === records.length && records.length > 0}
                    onChange={toggleAll} />
                </th>
                <th>Status</th>
                <th>Scope</th>
                <th>Category</th>
                <th>Period</th>
                <th>Quantity</th>
                <th>Source</th>
                <th>Flags</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {records.map(r => (
                <tr key={r.id} className={`${selected.has(r.id) ? 'row-selected' : ''} ${r.flag_reasons?.length ? 'row-flagged' : ''}`}>
                  <td>
                    <input type="checkbox" className="cb"
                      checked={selected.has(r.id)}
                      onChange={() => toggleSelect(r.id)} />
                  </td>
                  <td><StatusBadge status={r.status} /></td>
                  <td><ScopeBadge scope={r.scope} /></td>
                  <td className="cat-cell">{CAT_LABELS[r.category] || r.category}</td>
                  <td className="mono muted">{r.period_start}</td>
                  <td className="mono qty">{formatQty(r.quantity, r.quantity_unit)}</td>
                  <td><span className="source-chip">{SOURCE_LABELS[r.source_type] || r.source_type}</span></td>
                  <td>
                    {r.flag_reasons?.map((f, i) => (
                      <div key={i} className="flag-tag">
                        <AlertTriangle size={9} /> {f}
                      </div>
                    ))}
                  </td>
                  <td>
                    <Link to={`/review/${r.id}`} className="detail-link">
                      <ChevronRight size={14} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {count > 50 && (
        <div className="pagination">
          <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
          <span className="page-info">Page {page} of {Math.ceil(count / 50)}</span>
          <button className="page-btn" disabled={page >= Math.ceil(count / 50)} onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      )}

      {/* Reject modal */}
      {showRejectModal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowRejectModal(false)}>
          <div className="modal slide-in">
            <h3 className="modal-title">Reject {selected.size} record{selected.size !== 1 ? 's' : ''}</h3>
            <p className="modal-desc">A rejection reason is required for audit trail.</p>
            <textarea
              className="modal-textarea"
              placeholder="Enter rejection reason…"
              value={rejectNote}
              onChange={e => setRejectNote(e.target.value)}
              rows={3}
              autoFocus
            />
            <div className="modal-actions">
              <button className="modal-btn" onClick={() => setShowRejectModal(false)}>Cancel</button>
              <button className="modal-btn danger" onClick={handleReject} disabled={!rejectNote.trim() || actionLoading}>
                {actionLoading ? <Spinner size={13} /> : <XCircle size={13} />} Confirm Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}