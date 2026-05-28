export default function Spinner({ size = 18 }) {
  return (
    <div style={{
      width: size, height: size, border: `2px solid var(--border)`,
      borderTop: `2px solid var(--amber)`, borderRadius: '50%',
      animation: 'spin 0.7s linear infinite', display: 'inline-block',
    }} />
  )
}