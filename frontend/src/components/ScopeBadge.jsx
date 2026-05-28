export default function ScopeBadge({ scope }) {
  const colors = { '1': 'var(--scope1)', '2': 'var(--scope2)', '3': 'var(--scope3)' }
  const c = colors[scope] || 'var(--text-muted)'
  return (
    <span style={{
      fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 600,
      color: c, background: `${c}18`, border: `1px solid ${c}33`,
      padding: '2px 7px', borderRadius: '4px', whiteSpace: 'nowrap',
    }}>
      S{scope}
    </span>
  )
}