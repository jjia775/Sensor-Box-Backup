import type { Threshold } from '../../types/charts'

export default function ChartSVG({
  labels,
  data,
  thresholds,
  unit,
  title,
}: {
  labels: string[]
  data: number[]
  thresholds: Threshold[]
  unit: string
  title: string
}) {
  const width = 900
  const height = 320
  const padding = { left: 56, right: 16, top: 32, bottom: 40 }

  if (!labels.length || !data.length) {
    return (
      <div className="rounded-2xl bg-white border shadow p-4">
        <div className="text-lg font-semibold mb-1">{title}</div>
        <div className="text-sm text-gray-500">No data.</div>
      </div>
    )
  }

  const xs = labels.map((_, i) => i)
  const thrVals = thresholds.map(t => t.value)
  const minY = Math.min(...data, ...(thrVals.length ? thrVals : [Infinity]))
  const maxY = Math.max(...data, ...(thrVals.length ? thrVals : [-Infinity]))
  const y0 = minY === maxY ? minY - 1 : minY
  const y1 = minY === maxY ? maxY + 1 : maxY

  const xscale = (i: number) =>
    padding.left +
    (i / Math.max(1, data.length - 1)) * (width - padding.left - padding.right)
  const yscale = (v: number) =>
    padding.top + (1 - (v - y0) / (y1 - y0)) * (height - padding.top - padding.bottom)

  const path = xs
    .map((i, idx) => `${idx === 0 ? 'M' : 'L'} ${xscale(i).toFixed(2)} ${yscale(data[i]).toFixed(2)}`)
    .join(' ')

  const yTicks = 5
  const tickVals = Array.from({ length: yTicks + 1 }, (_, i) => y0 + (i * (y1 - y0)) / yTicks)

  const timeTicks = 6
  const xTickIdx = Array.from({ length: Math.min(timeTicks, labels.length) }, (_, i) =>
    Math.round((i * (labels.length - 1)) / Math.max(1, timeTicks - 1)),
  )

  return (
    <div className="rounded-2xl bg-white border shadow p-4 overflow-x-auto">
      <div className="flex items-center justify-between mb-2">
        <div className="text-lg font-semibold">{title}</div>
        <div className="text-sm text-gray-500">{unit && `Unit: ${unit}`}</div>
      </div>
      <svg width={width} height={height}>
        <rect x={0} y={0} width={width} height={height} fill="white" />
        {tickVals.map((v, i) => {
          const y = yscale(v)
          return (
            <g key={`grid-y-${i}`}>
              <line x1={padding.left} x2={width - padding.right} y1={y} y2={y} stroke="#eee" />
              <text x={padding.left - 8} y={y + 4} textAnchor="end" fontSize="10" fill="#6b7280">
                {v.toFixed(2)}
              </text>
            </g>
          )
        })}
        {xTickIdx.map((idx, i) => {
          const x = xscale(idx)
          const ts = new Date(labels[idx])
          const label =
            `${String(ts.getHours()).padStart(2, '0')}:${String(ts.getMinutes()).padStart(2, '0')}` +
            (i === 0 || ts.getHours() === 0 ? `\n${ts.getMonth() + 1}/${ts.getDate()}` : '')
          return (
            <g key={`grid-x-${i}`}>
              <line x1={x} x2={x} y1={padding.top} y2={height - padding.bottom} stroke="#f5f5f5" />
              <text x={x} y={height - padding.bottom + 12} textAnchor="middle" fontSize="10" fill="#6b7280">
                {label}
              </text>
            </g>
          )
        })}
        <path d={path} fill="none" stroke="#111827" strokeWidth={1.8} />
        {thresholds.map((t, i) => {
          const y = yscale(t.value)
          return (
            <g key={`thr-${i}`}>
              <line
                x1={padding.left}
                x2={width - padding.right}
                y1={y}
                y2={y}
                stroke={t.kind === 'upper' ? '#ef4444' : '#3b82f6'}
                strokeDasharray="4 4"
              />
              <text x={width - padding.right} y={y - 4} textAnchor="end" fontSize="10" fill="#6b7280">
                {t.label}: {t.value}
              </text>
            </g>
          )
        })}
        <line x1={padding.left} x2={width - padding.right} y1={height - padding.bottom} y2={height - padding.bottom} stroke="#e5e7eb" />
        <line x1={padding.left} x2={padding.left} y1={padding.top} y2={height - padding.bottom} stroke="#e5e7eb" />
      </svg>
    </div>
  )
}
