import { useState } from 'react'
import { INK, SEQUENTIAL_BLUE } from './palette'

const HEIGHT = 220
const PAD_LEFT = 32
const PAD_BOTTOM = 24
const PAD_TOP = 16

/**
 * Single-series line chart. `data`: [{ label, value }]. One series needs no
 * legend box — the title names it.
 */
function LineChart({ data, title, valueLabel = (v) => v }) {
  const [hover, setHover] = useState(null)
  const width = Math.max(data.length * 48, 360)
  const max = Math.max(1, ...data.map((d) => d.value))
  const plotWidth = width - PAD_LEFT - 8
  const plotHeight = HEIGHT - PAD_TOP - PAD_BOTTOM
  const stepX = data.length > 1 ? plotWidth / (data.length - 1) : 0
  const points = data.map((d, i) => ({
    x: PAD_LEFT + i * stepX,
    y: PAD_TOP + plotHeight - (d.value / max) * plotHeight,
    ...d,
  }))
  const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
  const ticks = [0, 0.5, 1].map((f) => Math.round(max * f))

  return (
    <div className="viz-root">
      {title && <h3 className="mb-1 text-sm font-medium text-gray-700">{title}</h3>}
      <svg viewBox={`0 0 ${width} ${HEIGHT}`} className="w-full" role="img" aria-label={title || 'Line chart'}>
        {ticks.map((t) => {
          const y = PAD_TOP + plotHeight - (t / max) * plotHeight
          return (
            <g key={t}>
              <line x1={PAD_LEFT} y1={y} x2={width - 8} y2={y} stroke={INK.gridline} strokeWidth={1} />
              <text x={0} y={y + 3} fontSize={10} fill={INK.muted}>
                {t}
              </text>
            </g>
          )
        })}
        <path d={path} fill="none" stroke={SEQUENTIAL_BLUE} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        {points.map((p, i) => (
          <g key={p.label}>
            {i === points.length - 1 && (
              <text x={p.x} y={p.y - 10} textAnchor="end" fontSize={11} fill={INK.secondary}>
                {valueLabel(p.value)}
              </text>
            )}
            <circle
              cx={p.x}
              cy={p.y}
              r={hover === i ? 5 : 4}
              fill={SEQUENTIAL_BLUE}
              stroke={INK.surface}
              strokeWidth={2}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover((h) => (h === i ? null : h))}
            />
            <text x={p.x} y={HEIGHT - 6} textAnchor="middle" fontSize={9} fill={INK.muted}>
              {p.label}
            </text>
          </g>
        ))}
        {hover !== null && (
          <g>
            <line
              x1={points[hover].x}
              y1={PAD_TOP}
              x2={points[hover].x}
              y2={PAD_TOP + plotHeight}
              stroke={INK.baseline}
              strokeWidth={1}
            />
            <rect
              x={Math.min(Math.max(points[hover].x - 30, 0), width - 60)}
              y={points[hover].y - 28}
              width={60}
              height={20}
              rx={4}
              fill={INK.primary}
            />
            <text
              x={Math.min(Math.max(points[hover].x, 30), width - 30)}
              y={points[hover].y - 14}
              textAnchor="middle"
              fontSize={10}
              fill="#fff"
            >
              {valueLabel(points[hover].value)}
            </text>
          </g>
        )}
      </svg>
    </div>
  )
}

export default LineChart
