import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { review as reviewApi, actions } from '../api/endpoints'
import StatusBadge from '../components/StatusBadge'
import ScopeBadge from '../components/ScopeBadge'
import Spinner from '../components/Spinner'
import { CheckCircle, XCircle, Edit3, ArrowLeft, AlertTriangle, Clock, User } from 'lucide-react'
import toast from 'react-hot-toast'
import './RecordDetail.css'

export default function RecordDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [record, setRecord] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editData, setEditData] = useState({})
  const [rejectNote, setRejectNote] = useState('')
  const [showReject, setShowReject] = useState(false)

  useEffect(() => {
    reviewApi.detail(id).then(r => {
      setRecord(r.data)
      setEditData({ quantity: r.data.quantity, quantity_unit: r.data.quantity_unit,
        period_start: r.data.period_start, period_end: r.data.period_end })
    }).finally(() => setLoading(false))
  }, [id])

  const handleApprove = async () => {
    setActionLoading(true)
    try {
      await actions.approve([id])
      toast.success('Record approved')
      navigate('/review')
    } catch { toast.error('Approval failed') }
    finally { setActionLoading(false) }
  }

  const handleReject = async () => {
    if (!rejectNote.trim()) return
    setActionLoading(true)
    try {
      await actions.reject([id], rejectNote)
      toast.success('Record rejected')
      navigate('/review')
    } catch { toast.error('Rejection failed') }
    finally { setActionLoading(false) }
  }

  const handleEdit = async () => {
    const note = prompt('Enter a note explaining this edit (required):')
    if (!note?.trim()) return
    setActionLoading(true)
    try {
      const { data } = await reviewApi.edit(id, { ...editData, note })
      setRecord(data); setEditMode(false)
      toast.success('Record updated')
    } catch (err) { toast.error(err.response?.data?.error || 'Edit failed') }
    finally { setActionLoading(false) }
  }

  const fmtDate = d => d ? new Date(d).toLocaleString() : '—'
  const fmtMeta = obj => Object.entries(obj || {})
    .filter(([, v]) => v !== '' && v !== null && v !== 0 && v !== false)

  if (loading) return <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:300 }}><Spinner size={28} /></div>
  if (!record) return <div style={{ color: 'var(--text-muted)', padding: 40 }}>Record not found.</div>

  return (
    <div className="detail-page fade-in">
      <div className="detail-nav">
        <Link to="/review" className="back-link"><ArrowLeft size={14} /> Review Queue</Link>
        <span className="detail-id">{record.id}</span>
      </div>

      <div className="detail-header">
        <div className="detail-title-row">
          <h1 className="page-title">{record.category_display}</h1>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <ScopeBadge scope={record.scope} />
            <StatusBadge status={record.status} />
          </div>
        </div>
        <div className="detail-subtitle">
          From <strong>{record.batch_filename}</strong> · {record.source_type_display}
          · Ingested {fmtDate(record.created_at)}
        </div>
      </div>

      {record.flag_reasons?.length > 0 && (
        <div className="flag-banner">
          <AlertTriangle size={14} />
          <div>
            <div className="flag-banner-title">This record has been flagged</div>
            {record.flag_reasons.map((f, i) => <div key={i} className="flag-banner-item">{f}</div>)}
          </div>
        </div>
      )}

      <div className="detail-grid">
        {/* Emission data */}
        <div className="detail-card">
          <div className="card-header">
            <span className="card-title">Emission Data</span>
            {record.status !== 'APPROVED' && record.status !== 'REJECTED' && (
              <button className="edit-toggle" onClick={() => setEditMode(e => !e)}>
                <Edit3 size={12} /> {editMode ? 'Cancel' : 'Edit'}
              </button>
            )}
          </div>

          {!editMode ? (
            <div className="data-grid">
              <DataRow label="Scope" value={record.scope_display} />
              <DataRow label="Category" value={record.category_display} />
              <DataRow label="Quantity" value={`${record.quantity} ${record.quantity_unit}`} mono />
              <DataRow label="Raw Input" value={`${record.raw_quantity} ${record.raw_unit}`} mono muted />
              <DataRow label="Period Start" value={record.period_start} mono />
              <DataRow label="Period End" value={record.period_end} mono />
            </div>
          ) : (
            <div className="edit-form">
              <EditField label="Quantity" type="number" value={editData.quantity} onChange={v => setEditData(d => ({...d, quantity: v}))} />
              <EditField label="Unit" value={editData.quantity_unit} onChange={v => setEditData(d => ({...d, quantity_unit: v}))} />
              <EditField label="Period Start" type="date" value={editData.period_start} onChange={v => setEditData(d => ({...d, period_start: v}))} />
              <EditField label="Period End" type="date" value={editData.period_end} onChange={v => setEditData(d => ({...d, period_end: v}))} />
              <button className="save-btn" onClick={handleEdit} disabled={actionLoading}>
                {actionLoading ? <Spinner size={12} /> : '✓'} Save Changes
              </button>
            </div>
          )}
        </div>

        {/* Source metadata */}
        <div className="detail-card">
          <div className="card-header"><span className="card-title">Source Metadata</span></div>
          <div className="data-grid">
            {fmtMeta(record.source_metadata).map(([k, v]) => (
              <DataRow key={k} label={k.replace(/_/g, ' ')} value={String(v)} mono={typeof v === 'number' || k.includes('id') || k.includes('code')} />
            ))}
          </div>
        </div>

        <div className="transform-grid">

  <div className="detail-card">

    <div className="section-title">
      Raw Source Data
    </div>

    <div className="meta-list">

      {Object.entries(record.source_metadata || {}).map(
        ([k, v]) => (

          <div className="meta-row" key={k}>

            <span className="meta-key">
              {k.replace(/_/g, ' ')}
            </span>

            <span className="meta-value">
              {String(v)}
            </span>

          </div>
        )
      )}

    </div>

  </div>

  <div className="detail-card">

    <div className="section-title">
      Normalized ESG Record
    </div>

    <div className="meta-list">

      <div className="meta-row">
        <span className="meta-key">Scope</span>
        <span className="meta-value">
          Scope {record.scope}
        </span>
      </div>

      <div className="meta-row">
        <span className="meta-key">Category</span>
        <span className="meta-value">
          {record.category}
        </span>
      </div>

      <div className="meta-row">
        <span className="meta-key">Quantity</span>
        <span className="meta-value">
          {record.quantity}
        </span>
      </div>

      <div className="meta-row">
        <span className="meta-key">Unit</span>
        <span className="meta-value">
          {record.quantity_unit}
        </span>
      </div>

      <div className="meta-row">
        <span className="meta-key">Status</span>
        <span className="meta-value">
          {record.status}
        </span>
      </div>

    </div>

  </div>

</div>

        {/* Review info */}
        <div className="detail-card">
          <div className="card-header"><span className="card-title">Review Status</span></div>
          <div className="data-grid">
            <DataRow label="Status" value={<StatusBadge status={record.status} />} />
            <DataRow label="Reviewed By" value={record.reviewed_by ? `${record.reviewed_by.first_name} ${record.reviewed_by.last_name}` : '—'} />
            <DataRow label="Reviewed At" value={record.reviewed_at ? fmtDate(record.reviewed_at) : '—'} />
            {record.reviewer_note && <DataRow label="Note" value={record.reviewer_note} />}
          </div>
        </div>

        {/* Audit trail */}
        <div className="detail-card audit-card">
          <div className="card-header"><span className="card-title">Audit Trail</span></div>
          <div className="audit-list">
            {record.audit_trail?.map(entry => (
              <div key={entry.id} className="audit-entry">
                <div className="audit-dot" data-action={entry.action} />
                <div className="audit-body">
                  <div className="audit-line">
                    <span className={`audit-action ${entry.action.toLowerCase()}`}>{entry.action}</span>
                    <span className="audit-actor">
                      <User size={10} /> {entry.actor?.first_name || 'System'}
                    </span>
                    <span className="audit-time"><Clock size={9} /> {fmtDate(entry.timestamp)}</span>
                  </div>
                  {entry.note && <div className="audit-note">{entry.note}</div>}
                </div>
              </div>
            ))}
            {!record.audit_trail?.length && <div className="audit-empty">No audit entries.</div>}
          </div>
        </div>
      </div>

      {/* Actions */}
      {(record.status === 'PENDING' || record.status === 'FLAGGED') && (
        <div className="action-bar">
          {!showReject ? (
            <>
              <button className="action-btn approve" onClick={handleApprove} disabled={actionLoading}>
                {actionLoading ? <Spinner size={14} /> : <CheckCircle size={15} />}
                Approve Record
              </button>
              <button className="action-btn reject" onClick={() => setShowReject(true)}>
                <XCircle size={15} /> Reject Record
              </button>
            </>
          ) : (
            <div className="reject-inline">
              <textarea
                className="reject-textarea" placeholder="Rejection reason (required)…"
                value={rejectNote} onChange={e => setRejectNote(e.target.value)} rows={2} autoFocus
              />
              <button className="action-btn reject" onClick={handleReject} disabled={!rejectNote.trim() || actionLoading}>
                {actionLoading ? <Spinner size={13} /> : <XCircle size={13} />} Confirm Reject
              </button>
              <button className="action-btn cancel" onClick={() => setShowReject(false)}>Cancel</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function DataRow({ label, value, mono, muted }) {
  return (
    <div className="data-row">
      <span className="data-label">{label}</span>
      <span className={`data-value ${mono ? 'mono' : ''} ${muted ? 'muted' : ''}`}>
        {value ?? '—'}
      </span>
    </div>
  )
}

function EditField({ label, type = 'text', value, onChange }) {
  return (
    <div className="edit-field">
      <label className="field-label">{label}</label>
      <input className="field-input" type={type} value={value ?? ''} onChange={e => onChange(e.target.value)} />
    </div>
  )
}