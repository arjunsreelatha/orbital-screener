function RiskBadge({ label }) {
  const colors = {
    HIGH:   { bg: '#ef4444', text: '#fff' },
    MEDIUM: { bg: '#f59e0b', text: '#000' },
    LOW:    { bg: '#22c55e', text: '#fff' },
  }
  const c = colors[label] || { bg: '#333', text: '#fff' }
  return (
    <span style={{
      background: c.bg,
      color: c.text,
      padding: '2px 8px',
      borderRadius: '4px',
      fontSize: '11px',
      fontWeight: 'bold'
    }}>
      {label}
    </span>
  )
}

function RiskTable({ conjunctions, onSelect }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: '13px',
        fontFamily: 'monospace'
      }}>
        <thead>
          <tr style={{ background: '#111', color: '#888' }}>
            <th style={th}>Risk</th>
            <th style={th}>Object 1</th>
            <th style={th}>Object 2</th>
            <th style={th}>Miss Dist (km)</th>
            <th style={th}>Rel Vel (km/s)</th>
            <th style={th}>Risk Score</th>
            <th style={th}>Snapshots</th>
          </tr>
        </thead>
        <tbody>
          {conjunctions.map((c, i) => (
            <tr
              key={i}
              onClick={() => onSelect(c)}
              style={{
                borderBottom: '1px solid #222',
                cursor: 'pointer',
                background: i % 2 === 0 ? '#0d0d0d' : '#111'
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#1a1a1a'}
              onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? '#0d0d0d' : '#111'}
            >
              <td style={td}><RiskBadge label={c.risk_label} /></td>
              <td style={td}>{c.object1_name}</td>
              <td style={td}>{c.object2_name}</td>
              <td style={td}>{c.miss_distance_km.toFixed(2)}</td>
              <td style={td}>{c.relative_velocity_km_s.toFixed(3)}</td>
              <td style={td}>{(c.risk_score * 100).toFixed(1)}%</td>
              <td style={td}>{c.snapshot_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const th = {
  padding: '10px 12px',
  textAlign: 'left',
  fontWeight: '500',
  borderBottom: '1px solid #333'
}

const td = {
  padding: '8px 12px',
  color: '#ccc'
}

export default RiskTable