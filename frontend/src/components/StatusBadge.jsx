import './StatusBadge.css'

const CONFIG = {
  PENDING:  { label: 'Pending',  cls: 'pending' },
  FLAGGED:  { label: 'Flagged',  cls: 'flagged' },
  APPROVED: { label: 'Approved', cls: 'approved' },
  REJECTED: { label: 'Rejected', cls: 'rejected' },
  DONE:     { label: 'Done',     cls: 'approved' },
  FAILED:   { label: 'Failed',   cls: 'rejected' },
  PROCESSING:{ label: 'Processing', cls: 'pending' },
}

export default function StatusBadge({ status }) {
  const c = CONFIG[status] || { label: status, cls: 'pending' }
  return <span className={`status-badge ${c.cls}`}>{c.label}</span>
}


