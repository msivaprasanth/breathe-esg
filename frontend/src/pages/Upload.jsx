import { useState, useRef } from 'react'
import { upload as uploadApi } from '../api/endpoints'
import { Upload, FileText, CheckCircle, AlertTriangle, X, ChevronDown } from 'lucide-react'
import Spinner from '../components/Spinner'
import './Upload.css'

const SOURCE_TYPES = [
  {
    value: 'SAP_FUEL_PROCUREMENT',
    label: 'SAP Fuel & Procurement',
    desc: 'MB51 / ME2L flat-file export. Handles German headers, DD.MM.YYYY dates, unit normalization.',
    scope: 'Scope 1 + 3',
    accept: '.csv,.xlsx,.xls',
    example: 'sap_mb51_export.csv',
  },
  {
    value: 'UTILITY_ELECTRICITY',
    label: 'Utility Electricity',
    desc: 'Portal CSV export (BESCOM, Tata Power, Green Button). Handles billing periods spanning months.',
    scope: 'Scope 2',
    accept: '.csv,.xlsx,.xls',
    example: 'utility_q1_2024.csv',
  },
  {
    value: 'CORPORATE_TRAVEL',
    label: 'Corporate Travel',
    desc: 'Concur / Navan expense report CSV. Resolves IATA codes to distances, maps travel categories.',
    scope: 'Scope 3',
    accept: '.csv,.xlsx,.xls',
    example: 'concur_trip_report.csv',
  },
]

export default function UploadPage() {
  const [sourceType, setSourceType] = useState('')
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const fileRef = useRef()

  const selected = SOURCE_TYPES.find(s => s.value === sourceType)

  const handleFile = f => {
    if (!f) return
    setFile(f); setResult(null); setError('')
  }

  const handleDrop = e => {
    e.preventDefault(); setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleSubmit = async () => {
    if (!file || !sourceType) return
    setUploading(true); setProgress(0); setResult(null); setError('')
    try {
      const { data } = await uploadApi.ingest(file, sourceType, setProgress)
      setResult(data)
      setFile(null)
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed. Check the file format.')
    } finally {
      setUploading(false)
    }
  }

  const reset = () => { setFile(null); setResult(null); setError(''); setProgress(0) }

  return (
    <div className="upload-page fade-in">
      <div className="page-header">
        <h1 className="page-title">Ingest Data</h1>
        <p className="page-subtitle">Upload emissions source files for parsing, normalization, and analyst review.</p>
      </div>

      <div className="upload-layout">
        {/* Source type selector */}
        <div className="source-selector">
          <div className="section-label">1 — SELECT DATA SOURCE</div>
          {SOURCE_TYPES.map(s => (
            <div
              key={s.value}
              className={`source-option ${sourceType === s.value ? 'active' : ''}`}
              onClick={() => { setSourceType(s.value); reset() }}
            >
              <div className="source-option-header">
                <span className="source-option-label">{s.label}</span>
                <span className={`scope-tag ${s.scope.toLowerCase().replace(/[^a-z0-9]/g,'')}`}>{s.scope}</span>
              </div>
              <p className="source-option-desc">{s.desc}</p>
            </div>
          ))}
        </div>

        {/* Upload zone */}
        <div className="upload-zone-wrap">
          <div className="section-label">2 — UPLOAD FILE</div>

          {!sourceType && (
            <div className="upload-placeholder">
              <ChevronDown size={20} style={{ color: 'var(--text-muted)' }} />
              <span>Select a data source first</span>
            </div>
          )}

          {sourceType && !result && (
            <>
              <div
                className={`drop-zone ${dragging ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
                onDragOver={e => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => !file && fileRef.current.click()}
              >
                <input
                  ref={fileRef}
                  type="file"
                  accept={selected?.accept}
                  style={{ display: 'none' }}
                  onChange={e => handleFile(e.target.files[0])}
                />

                {!file ? (
                  <div className="drop-empty">
                    <div className="drop-icon"><Upload size={22} strokeWidth={1.5} /></div>
                    <div className="drop-main">Drop file here or <span className="drop-link">browse</span></div>
                    <div className="drop-hint">{selected?.accept?.replace(/\./g, '').toUpperCase()}</div>
                    <div className="drop-example">e.g. {selected?.example}</div>
                  </div>
                ) : (
                  <div className="file-selected">
                    <FileText size={20} style={{ color: 'var(--amber)', flexShrink: 0 }} />
                    <div className="file-details">
                      <div className="file-name">{file.name}</div>
                      <div className="file-size">{(file.size / 1024).toFixed(1)} KB</div>
                    </div>
                    <button className="file-remove" onClick={e => { e.stopPropagation(); setFile(null) }}>
                      <X size={13} />
                    </button>
                  </div>
                )}
              </div>

              {error && (
                <div className="upload-error">
                  <AlertTriangle size={13} /> {error}
                </div>
              )}

              {uploading && (
                <div className="progress-wrap">
                  <div className="progress-track">
                    <div className="progress-bar" style={{ width: `${progress}%` }} />
                  </div>
                  <span className="progress-label">{progress}%</span>
                </div>
              )}

              <button
                className="upload-submit"
                onClick={handleSubmit}
                disabled={!file || uploading}
              >
                {uploading ? <><Spinner size={14} /> Parsing...</> : <><Upload size={14} /> Ingest File</>}
              </button>
            </>
          )}

          {/* Result card */}
          {result && (
            <div className={`result-card ${result.status === 'DONE' ? 'success' : 'error'} slide-in`}>
              <div className="result-header">
                {result.status === 'DONE'
                  ? <CheckCircle size={18} style={{ color: 'var(--green)' }} />
                  : <AlertTriangle size={18} style={{ color: 'var(--red)' }} />
                }
                <span className="result-title">
                  {result.status === 'DONE' ? 'Ingestion Complete' : 'Ingestion Failed'}
                </span>
              </div>

              <div className="result-stats">
                <div className="res-stat"><span className="res-num">{result.parsed_rows}</span><span className="res-lbl">Parsed</span></div>
                <div className="res-stat flagged"><span className="res-num">{result.flagged_rows}</span><span className="res-lbl">Flagged</span></div>
                <div className="res-stat error"><span className="res-num">{result.failed_rows}</span><span className="res-lbl">Failed</span></div>
              </div>

              {result.parse_errors?.length > 0 && (
                <div className="result-errors">
                  <div className="err-label">Parse errors (first {result.parse_errors.length}):</div>
                  {result.parse_errors.slice(0, 5).map((e, i) => (
                    <div key={i} className="err-row">
                      <span className="err-row-num">Row {e.row}</span>
                      <span className="err-row-msg">{e.error}</span>
                    </div>
                  ))}
                </div>
              )}

              <div className="result-actions">
                <button className="result-btn primary" onClick={() => window.location.href = '/review?status=PENDING'}>
                  Go to Review Queue
                </button>
                <button className="result-btn" onClick={() => { reset(); setSourceType('') }}>
                  Upload Another
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}