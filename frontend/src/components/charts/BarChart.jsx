import { useState } from 'react'
import { CATEGORICAL, INK } from './palette'

const HEIGHT = 220
const BAR_MAX_WIDTH = 24
const GAP = 2

/**
 * Vertical categorical bar chart. `data`: [{ label, value }]. One color per
 * category from the fixed palette slot order — never cycled or re-sorted.
 */
function BarChart({ data, valueLabel = (v) => v, title, showTable = true }) {
  const [tableOpen, setTableOpen] = useState(false)
  const max = Math.max(1, ...data.map((d) => d.value))
  const width = Math.max(data.length * 56, 320)
  const bandWidth = width / data.length
  const barWidth = Math.min(BAR_MAX_WIDTH, bandWidth - GAP * 2)
  const baselineY = HEIGHT - 28

  return (
    <div className="viz-root">
      {title && <h3 className="mb-1 text-sm font-medium text-gray-700">{title}</h3>}
      <svg viewBox={`0 0 ${width} ${HEIGHT}`} className="w-full" role="img" aria-label={title || 'Bar chart'}>
        <line x1={0} y1={baselineY} x2={width} y2={baselineY} stroke={INK.baseline} strokeWidth={1} />
        {data.map((d, i) => {
          const barHeight = (d.value / max) * (baselineY - 24)
          const x = i * bandWidth + (bandWidth - barWidth) / 2
          const y = baselineY - barHeight
          const color = CATEGORICAL[i % CATEGORICAL.length]
          return (
            <g key={d.label}>
              <title>{`${d.label}: ${valueLabel(d.value)}`}</title>
              <rect x={x} y={y} width={barWidth} height={Math.max(barHeight, 0)} rx={4} fill={color} />
              <text x={x + barWidth / 2} y={y - 6} textAnchor="middle" fontSize={11} fill={INK.secondary}>
                {valueLabel(d.value)}
              </text>
              <text x={x + barWidth / 2} y={baselineY + 16} textAnchor="middle" fontSize={11} fill={INK.muted}>
                {d.label}
              </text>
            </g>
          )
        })}
      </svg>
      {showTable && (
        <button
          type="button"
          onClick={() => setTableOpen((v) => !v)}
          className="mt-1 text-xs text-red-700 underline"
        >
          {tableOpen ? 'Hide table' : 'View as table'}
        </button>
      )}
      {tableOpen && (
        <table className="mt-2 w-full text-left text-xs">
          <thead className="text-gray-500">
            <tr>
              <th className="py-1 pr-2 font-medium">Category</th>
              <th className="py-1 font-medium">Value</th>
            </tr>
          </thead>
          <tbody>
            {data.map((d) => (
              <tr key={d.label} className="border-t border-gray-100">
                <td className="py-1 pr-2">{d.label}</td>
                <td className="py-1">{valueLabel(d.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default BarChart
