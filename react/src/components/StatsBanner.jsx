function StatsBanner({ conjunctions }) {
  const high = conjunctions.filter(c => c.risk_label === 'HIGH').length
  const medium = conjunctions.filter(c => c.risk_label === 'MEDIUM').length
  const low = conjunctions.filter(c => c.risk_label === 'LOW').length

  return (
    <div style={{
      display: 'flex',
      gap: '20px',
      marginBottom: '24px',
      padding: '16px',
      background: '#0a0a0a',
      borderRadius: '8px',
      border: '1px solid #222'
    }}>
      <StatCard label="Total Pairs" value={conjunctions.length} color="#ffffff" />
      <StatCard label="HIGH Risk" value={high} color="#ef4444" />
      <StatCard label="MEDIUM Risk" value={medium} color="#f59e0b" />
      <StatCard label="LOW Risk" value={low} color="#22c55e" />
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div style={{
      flex: 1,
      textAlign: 'center',
      padding: '12px',
      border: '1px solid #333',
      borderRadius: '6px',
      background: '#111'
    }}>
      <div style={{ fontSize: '28px', fontWeight: 'bold', color }}>{value}</div>
      <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>{label}</div>
    </div>
  )
}

export default StatsBanner