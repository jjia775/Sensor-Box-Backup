import type { Sensor } from '../types/sensors'

export default function SensorCard({ x }: { x: Sensor }) {
  return (
    <div className="rounded-2xl bg-white shadow p-4 border">
      <div className="flex items-center justify-between">
        <div className="text-lg font-semibold">{x.name}</div>
        <span className="text-xs rounded-full border px-2 py-1">{x.type}</span>
      </div>
      <div className="mt-2 text-sm text-gray-600">Location: {x.location || '-'}</div>
      <div className="mt-3">
        <div className="text-sm font-medium mb-1">Meta</div>
        <pre className="text-xs bg-gray-50 rounded-xl p-3 overflow-auto">
          {JSON.stringify(x.meta ?? {}, null, 2)}
        </pre>
      </div>
    </div>
  )
}
