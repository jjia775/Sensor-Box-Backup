import SensorCard from './SensorCard'
import type { Sensor } from '../types/sensors'

export default function SensorGrid({ items }: { items: Sensor[] }) {
  if (!items.length) {
    return <div className="text-gray-600">No sensors found.</div>
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map(x => (
        <SensorCard key={x.id} x={x} />
      ))}
    </div>
  )
}
