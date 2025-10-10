export type Sensor = {
  id: string
  name: string
  type: string
  location?: string | null
  meta?: Record<string, unknown> | null
  serial_number?: string | null   // ← 新增
}
