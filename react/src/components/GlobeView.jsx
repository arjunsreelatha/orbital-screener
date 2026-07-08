import { useEffect, useRef } from 'react'
import * as Cesium from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'

Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJmMzM5ODY1YS0xMjlmLTQwODYtODk3OC01NWZjZjI4ZWM3OGEiLCJpZCI6NDUwMzQ1LCJzdWIiOiJhcmp1bnNyZWVsYXRoYSIsImlzcyI6Imh0dHBzOi8vYXBpLmNlc2l1bS5jb20iLCJhdWQiOiJvcmJpdGFsLXNjcmVlbmVyIiwiaWF0IjoxNzgyNzMyODc0fQ.6axf9gYEmLdUFVjnHc9AoObPkwyEFhMhutAXQNtdwu0'

function GlobeView({ conjunctions }) {
  const cesiumContainer = useRef(null)
  const viewerRef = useRef(null)

  useEffect(() => {
    if (viewerRef.current) return

    const viewer = new Cesium.Viewer(cesiumContainer.current, {
      timeline: false,
      animation: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      navigationHelpButton: false,
      fullscreenButton: false,
    })

    viewerRef.current = viewer

    // fetch and plot satellite positions
    fetch('http://localhost:8000/positions')
      .then(res => res.json())
      .then(satellites => {
        if (!viewerRef.current || viewerRef.current.isDestroyed()) return
        satellites.forEach(sat => {
          viewerRef.current.entities.add({
            name: sat.name,
            position: Cesium.Cartesian3.fromDegrees(sat.lon, sat.lat, sat.alt * 1000),
            point: {
              pixelSize: 3,
              color: Cesium.Color.CYAN,
              outlineColor: Cesium.Color.WHITE,
              outlineWidth: 1,
            },
            label: {
              text: sat.name,
              show: false,
              font: '10px monospace',
              fillColor: Cesium.Color.WHITE,
            }
          })
        })
        console.log(`Plotted ${satellites.length} satellites`)
      })

    // fetch and plot conjunction lines
    fetch('http://localhost:8000/conjunction_lines')
      .then(res => res.json())
      .then(lines => {
        if (!viewerRef.current || viewerRef.current.isDestroyed()) return
        lines.forEach(line => {
          viewerRef.current.entities.add({
          polyline: {
              positions: Cesium.Cartesian3.fromDegreesArrayHeights([
                line.pos1.lon, line.pos1.lat, line.pos1.alt * 1000,
                line.pos2.lon, line.pos2.lat, line.pos2.alt * 1000,
              ]),
              width: 5,
              material: new Cesium.PolylineGlowMaterialProperty({
                glowPower: 0.3,
                color: Cesium.Color.RED,
              }),
            }
          })
        })
        if (lines.length > 0)
        {
          const line = lines[0]
          viewerRef.current.camera.flyTo({
            destination:  Cesium.Cartesian3.fromDegrees(
              line.pos1.lon, line.pos1.lat, line.pos1.alt * 1000 + 500000),
            duration: 3
          })
        }
        console.log(`Plotted ${lines.length} conjunction lines`)
      })

    return () => {
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        viewerRef.current.destroy()
        viewerRef.current = null
      }
    }
  }, [])

  return (
    <div
      ref={cesiumContainer}
      style={{ width: '100%', height: '500px', borderRadius: '8px', overflow: 'hidden' }}
    />
  )
}

export default GlobeView