import { useState, useEffect } from 'react'
import StatsBanner from './components/StatsBanner'
import RiskTable from './components/RiskTable'
import GlobeView from './components/GlobeView'
function App() {
  const [conjunctions, setConjunctions] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    fetch('http://localhost:8000/conjunctions?limit=10000')
      .then(res => res.json())
      .then(data => {
        setConjunctions(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('API error:', err)
        setLoading(false)
      })
  }, [])

  return (
    <div style={{
      minHeight: '100vh',
      background: '#080808',
      color: '#fff',
      padding: '24px',
      fontFamily: 'monospace'
    }}>
      <h1 style={{ margin: '0 0 8px 0', fontSize: '22px', color: '#fff' }}>
        🛰️ Orbital Screener
      </h1>
      <p style={{ margin: '0 0 20px 0', color: '#555', fontSize: '13px' }}>
        AI-powered conjunction risk assessment — Starlink constellation
      </p>

      {loading ? (
        <p style={{ color: '#555' }}>Loading conjunctions...</p>
      ) : (
        <>
            <StatsBanner conjunctions={conjunctions} />
            <GlobeView conjunctions={conjunctions} />
          <RiskTable conjunctions={conjunctions} onSelect={setSelected} />
        </>
      )}

      {selected && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}
          onClick={() => setSelected(null)}
        >
          <div style={{
            background: '#111',
            border: '1px solid #333',
            borderRadius: '8px',
            padding: '24px',
            minWidth: '400px',
            maxWidth: '600px'
          }}
            onClick={e => e.stopPropagation()}
          >
            <h2 style={{ margin: '0 0 16px 0', fontSize: '16px' }}>
              Conjunction Detail
            </h2>
            <table style={{ width: '100%', fontSize: '13px' }}>
              <tbody>
                {Object.entries(selected).map(([k, v]) => (
                  <tr key={k} style={{ borderBottom: '1px solid #222' }}>
                    <td style={{ padding: '6px 0', color: '#888', width: '50%' }}>{k}</td>
                    <td style={{ padding: '6px 0', color: '#fff' }}>
                      {typeof v === 'number' ? v.toFixed(4) : String(v)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button
              onClick={() => setSelected(null)}
              style={{
                marginTop: '16px',
                padding: '8px 16px',
                background: '#333',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App