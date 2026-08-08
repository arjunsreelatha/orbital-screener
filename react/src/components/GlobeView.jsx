
import { useEffect, useRef } from 'react'
import * as Cesium from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'
Cesium.Ion.defaultAccessToken = import.meta.env.VITE_CESIUM_TOKEN

function GlobeView({ conjunctions, refreshKey }) {
  const cesiumContainer = useRef(null)
  const viewerRef = useRef(null)

  // Create Cesium viewer only once
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

    return () => {
      if (
        viewerRef.current &&
        !viewerRef.current.isDestroyed()
      ) {
        viewerRef.current.destroy()
        viewerRef.current = null
      }
    }
  }, [])

  // Reload orbital data after refresh
  useEffect(() => {
    if (!viewerRef.current) return

    const viewer = viewerRef.current

    // Remove old satellites and conjunction lines
    viewer.entities.removeAll()

    // Fetch latest satellite positions
    fetch('http://localhost:8000/positions')
      .then(res => {
        if (!res.ok) {
          throw new Error('Failed to load satellite positions')
        }

        return res.json()
      })
      .then(satellites => {
        if (
          !viewerRef.current ||
          viewerRef.current.isDestroyed()
        ) {
          return
        }

        satellites.forEach(sat => {
          viewer.entities.add({
            name: sat.name,

            position: Cesium.Cartesian3.fromDegrees(
              sat.lon,
              sat.lat,
              sat.alt * 1000
            ),

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

        console.log(
          `Plotted ${satellites.length} satellites`
        )
      })
      .catch(err => {
        console.error(
          'Satellite position error:',
          err
        )
      })

    // Fetch latest conjunction lines
    fetch('http://localhost:8000/conjunction_lines')
      .then(res => {
        if (!res.ok) {
          throw new Error(
            'Failed to load conjunction lines'
          )
        }

        return res.json()
      })
      .then(lines => {
        if (
          !viewerRef.current ||
          viewerRef.current.isDestroyed()
        ) {
          return
        }

        lines.forEach(line => {
          viewer.entities.add({
            polyline: {
              positions:
                Cesium.Cartesian3.fromDegreesArrayHeights([
                  line.pos1.lon,
                  line.pos1.lat,
                  line.pos1.alt * 1000,

                  line.pos2.lon,
                  line.pos2.lat,
                  line.pos2.alt * 1000,
                ]),

              width: 5,

              material:
                new Cesium.PolylineGlowMaterialProperty({
                  glowPower: 0.3,
                  color: Cesium.Color.RED,
                }),
            }
          })
        })

        if (lines.length > 0) {
          const line = lines[0]

          viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(
              line.pos1.lon,
              line.pos1.lat,
              line.pos1.alt * 1000 + 500000
            ),
            duration: 3
          })
        }

        console.log(
          `Plotted ${lines.length} conjunction lines`
        )
      })
      .catch(err => {
        console.error(
          'Conjunction line error:',
          err
        )
      })

  }, [refreshKey])

  return (
    <div
      ref={cesiumContainer}
      style={{
        width: '100%',
        height: '500px',
        borderRadius: '8px',
        overflow: 'hidden'
      }}
    />
  )
}

export default GlobeView