import { useState, useEffect } from 'react'
import StatsBanner from './components/StatsBanner'
import RiskTable from './components/RiskTable'
import GlobeView from './components/GlobeView'

function App() {
  const [conjunctions, setConjunctions] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  const [refreshing, setRefreshing] = useState(false)
  const [refreshStatus, setRefreshStatus] = useState("")

  const [globeRefreshKey, setGlobeRefreshKey] = useState(0)

  const loadConjunctions = async () => {
    try {
      setLoading(true)

      const res = await fetch(
        "http://localhost:8000/conjunctions?limit=10000"
      )

      if (!res.ok) {
        throw new Error("Failed to load conjunctions")
      }

      const data = await res.json()

      setConjunctions(data)

    } catch (err) {
      console.error("API error:", err)
    } finally {
      setLoading(false)
    }
  }

  const refreshData = async () => {
    try {
      setRefreshing(true)
      setRefreshStatus("Refreshing TLEs...")

      const res = await fetch("http://localhost:8000/refresh", {
        method: "POST",
      })

      if (!res.ok) {
        throw new Error("Failed to start refresh")
      }

      const interval = setInterval(async () => {
        try {
          const statusRes = await fetch(
            "http://localhost:8000/refresh/status"
          )

          const status = await statusRes.json()

          if (status.running) {
            setRefreshStatus("Running propagation and ML pipeline...")
            return
          }

          clearInterval(interval)

          if (status.last_error) {
            setRefreshStatus("Refresh Failed ❌")
            setRefreshing(false)
            return
          }

          setRefreshStatus("Refresh Complete ✅")

          // Reload conjunction data
          await loadConjunctions()

          // Tell Cesium to reload positions and lines
          setGlobeRefreshKey(prev => prev + 1)

          setRefreshing(false)

        } catch (err) {
          clearInterval(interval)

          console.error("Status error:", err)
          setRefreshStatus("Refresh Failed ❌")
          setRefreshing(false)
        }
      }, 2000)

    } catch (err) {
      console.error("Refresh error:", err)

      setRefreshStatus("Refresh Failed ❌")
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadConjunctions()
  }, [])

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#080808',
        color: '#fff',
        padding: '24px',
        fontFamily: 'monospace'
      }}
    >

      <h1
        style={{
          margin: '0 0 8px 0',
          fontSize: '22px',
          color: '#fff'
        }}
      >
        🛰️ Orbital Screener
      </h1>

      <p
        style={{
          margin: '0 0 20px 0',
          color: '#555',
          fontSize: '13px'
        }}
      >
        AI-powered conjunction risk assessment — Starlink constellation
      </p>

      {/* Refresh controls */}
      <div style={{ marginBottom: "20px" }}>

        <button
          onClick={refreshData}
          disabled={refreshing}
          style={{
            padding: "10px 18px",
            background: refreshing ? "#555" : "#1976d2",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: refreshing ? "not-allowed" : "pointer",
            fontWeight: "bold"
          }}
        >
          {refreshing
            ? "Refreshing..."
            : "Fetch Latest TLEs"}
        </button>

        {refreshStatus && (
          <p
            style={{
              marginTop: "10px",
              color: "#aaa"
            }}
          >
            {refreshStatus}
          </p>
        )}

      </div>

      {loading ? (

        <p style={{ color: '#555' }}>
          Loading conjunctions...
        </p>

      ) : (

        <>
          <StatsBanner
            conjunctions={conjunctions}
          />

          <GlobeView
            conjunctions={conjunctions}
            refreshKey={globeRefreshKey}
          />

          <RiskTable
            conjunctions={conjunctions}
            onSelect={setSelected}
          />
        </>

      )}

      {selected && (

        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
          onClick={() => setSelected(null)}
        >

          <div
            style={{
              background: '#111',
              border: '1px solid #333',
              borderRadius: '8px',
              padding: '24px',
              minWidth: '400px',
              maxWidth: '600px'
            }}
            onClick={e => e.stopPropagation()}
          >

            <h2
              style={{
                margin: '0 0 16px 0',
                fontSize: '16px'
              }}
            >
              Conjunction Detail
            </h2>

            <table
              style={{
                width: '100%',
                fontSize: '13px'
              }}
            >

              <tbody>

                {Object.entries(selected).map(([k, v]) => (

                  <tr
                    key={k}
                    style={{
                      borderBottom: '1px solid #222'
                    }}
                  >

                    <td
                      style={{
                        padding: '6px 0',
                        color: '#888',
                        width: '50%'
                      }}
                    >
                      {k}
                    </td>

                    <td
                      style={{
                        padding: '6px 0',
                        color: '#fff'
                      }}
                    >
                      {typeof v === 'number'
                        ? v.toFixed(4)
                        : String(v)}
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