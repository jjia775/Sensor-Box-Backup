import { useEffect, useMemo, useState } from 'react'
import type { MetricInfo, MetricsResp, TimeseriesResp } from '../../types/charts'
import type { Sensor } from '../../types/sensors'
import ChartSVG from './ChartSVG'

function formatISO(d: Date) {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

type Agg = 'avg' | 'min' | 'max' | 'last' | 'sum'
type RangeOpt = '6h' | '12h' | '24h'

// 本地找序列号的兜底逻辑：字段优先级 serial_number > meta.serial_number > meta.serial > meta.sn
function getSerial(s: Sensor): string {
  const direct = (s as any).serial_number
  if (typeof direct === 'string' && direct) return direct
  const m = (s.meta || {}) as any
  if (typeof m.serial_number === 'string' && m.serial_number) return m.serial_number
  if (typeof m.serial === 'string' && m.serial) return m.serial
  if (typeof m.sn === 'string' && m.sn) return m.sn
  return ''
}

// （可选）前端展示名映射；key 要与后端 /api/charts/metrics 对齐
const LABELS: Record<string, string> = {
  temp: '温度',
  co2: 'CO₂',
  pm25: 'PM2.5',
  rh: '相对湿度',
  no2: '二氧化氮',
  co: '一氧化碳',
  o2: '氧气',
  light_night: '夜间光照',
  noise_night: '夜间噪声',
}

export default function ChartsPanel({
  apiBase,
  houseId,
  allowedMetrics, // 新增：疾病关联的允许 metrics（如 ['temp','co2']）
}: {
  apiBase: string
  houseId: string
  allowedMetrics?: string[]
}) {
  // 服务器返回的“全部可用 metrics”
  const [allMetrics, setAllMetrics] = useState<MetricInfo[]>([])
  // 当前选中的 metric
  const [metric, setMetric] = useState<string>('')

  // Serial 选择
  const [serials, setSerials] = useState<string[]>([])
  const [serial, setSerial] = useState<string>('')

  // 其他查询参数
  const [interval, setInterval] = useState<string>('5m')
  const [agg, setAgg] = useState<Agg>('avg')
  const [range, setRange] = useState<RangeOpt>('24h')

  // 时序数据与状态
  const [tsLoading, setTsLoading] = useState(false)
  const [tsError, setTsError] = useState<string | null>(null)
  const [tsData, setTsData] = useState<TimeseriesResp | null>(null)

  // 拉全部 metrics
  useEffect(() => {
    let alive = true
    fetch(`${apiBase}/api/charts/metrics`)
      .then(async r => {
        if (!r.ok) throw new Error(await r.text())
        return r.json()
      })
      .then((d: MetricsResp) => {
        if (!alive) return
        setAllMetrics(d.metrics || [])
      })
      .catch(() => {
        setAllMetrics([]) // 拉取失败时为空（下方还会有兜底 UI）
      })
    return () => { alive = false }
  }, [apiBase])

  // 根据 allowedMetrics 过滤可选指标
  const filteredMetrics = useMemo<MetricInfo[]>(() => {
    if (!allMetrics?.length) return []
    if (!allowedMetrics || allowedMetrics.length === 0) return allMetrics
    const allow = new Set(allowedMetrics)
    return allMetrics.filter(m => allow.has(m.metric))
  }, [allMetrics, allowedMetrics])

  // 当可选指标变化时，若当前 metric 不在其中，则切换到第一个
  useEffect(() => {
    if (!filteredMetrics.length) {
      setMetric('')
      return
    }
    if (!metric || !filteredMetrics.find(m => m.metric === metric)) {
      setMetric(filteredMetrics[0].metric)
    }
  }, [filteredMetrics]) // eslint-disable-line react-hooks/exhaustive-deps

  // 拉取该住户下的所有传感器并提取唯一的 serial 列表
  useEffect(() => {
    if (!houseId) {
      setSerials([]); setSerial('')
      return
    }
    fetch(`${apiBase}/sensors/?house_id=${encodeURIComponent(houseId)}`)
      .then(async r => {
        if (!r.ok) throw new Error(await r.text())
        return r.json()
      })
      .then((arr: Sensor[]) => {
        const uniq: string[] = []
        const seen = new Set<string>()
        for (const s of arr) {
          const sn = getSerial(s)
          if (sn && !seen.has(sn)) {
            seen.add(sn)
            uniq.push(sn)
          }
        }
        setSerials(uniq)
        const key = `sensor_serial:${houseId}`
        const prev = localStorage.getItem(key)
        const initial = prev && uniq.includes(prev) ? prev : uniq[0] || ''
        setSerial(initial)
      })
      .catch(() => {
        setSerials([]); setSerial('')
      })
  }, [apiBase, houseId])

  // 发请求拿时序
  const loadTimeseries = async () => {
    setTsLoading(true); setTsError(null); setTsData(null)
    try {
      if (!serial) throw new Error('No sensor serial available')
      if (!metric) throw new Error('No metric available (check disease settings)')

      const now = new Date()
      const end = now
      const start = new Date(
        range === '24h' ? now.getTime() - 24 * 3600_000
        : range === '12h' ? now.getTime() - 12 * 3600_000
        : now.getTime() - 6 * 3600_000
      )

      const payload = {
        serial_number: serial, // ← 用 Serial ID 搜索
        metric,
        start_ts: formatISO(start),
        end_ts: formatISO(end),
        interval,
        agg,
        title: `${(LABELS[metric] ?? metric.toUpperCase())} (${interval}, ${agg})`,
      }

      const r = await fetch(`${apiBase}/api/charts/metric_timeseries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!r.ok) throw new Error(await r.text())
      const d: TimeseriesResp = await r.json()
      setTsData(d)
      localStorage.setItem(`sensor_serial:${houseId}`, serial)
    } catch (e: any) {
      setTsError(e?.message || 'Failed to load timeseries')
    } finally {
      setTsLoading(false)
    }
  }

  // UI：没有 metrics 的场景（例如 disease 配置过窄）
  const noMetricReason = useMemo(() => {
    if ((allMetrics?.length || 0) === 0) return '未能加载可用指标'
    if (allowedMetrics && allowedMetrics.length > 0 && filteredMetrics.length === 0) return '当前疾病未关联任何可用指标'
    return ''
  }, [allMetrics, allowedMetrics, filteredMetrics])

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-white border shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {/* Serial 选择 */}
          <div>
            <label className="block text-sm font-medium mb-1">Sensor Serial</label>
            <select
              className="w-full rounded-xl border px-3 py-2"
              value={serial}
              onChange={e => setSerial(e.target.value)}
            >
              {serials.length === 0 && <option value="">No serials</option>}
              {serials.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Metric 选择（已按 allowedMetrics 过滤） */}
          <div>
            <label className="block text-sm font-medium mb-1">Metric</label>
            <select
              className="w-full rounded-xl border px-3 py-2"
              value={metric}
              onChange={e => setMetric(e.target.value)}
              disabled={filteredMetrics.length === 0}
            >
              {filteredMetrics.length === 0 && <option value="">No metrics</option>}
              {filteredMetrics.map(m => (
                <option key={m.metric} value={m.metric}>
                  {LABELS[m.metric] ?? m.metric.toUpperCase()}
                </option>
              ))}
            </select>
            {noMetricReason && (
              <div className="mt-1 text-xs text-amber-700">{noMetricReason}</div>
            )}
          </div>

          {/* Interval */}
          <div>
            <label className="block text-sm font-medium mb-1">Interval</label>
            <select className="w-full rounded-xl border px-3 py-2" value={interval} onChange={e => setInterval(e.target.value)}>
              <option value="1m">1m</option>
              <option value="5m">5m</option>
              <option value="15m">15m</option>
              <option value="1h">1h</option>
            </select>
          </div>

          {/* Aggregate */}
          <div>
            <label className="block text-sm font-medium mb-1">Aggregate</label>
            <select className="w-full rounded-xl border px-3 py-2" value={agg} onChange={e => setAgg(e.target.value as Agg)}>
              <option value="avg">avg</option>
              <option value="min">min</option>
              <option value="max">max</option>
              <option value="last">last</option>
              <option value="sum">sum</option>
            </select>
          </div>

          {/* Range */}
          <div>
            <label className="block text-sm font-medium mb-1">Range</label>
            <select className="w-full rounded-xl border px-3 py-2" value={range} onChange={e => setRange(e.target.value as RangeOpt)}>
              <option value="6h">Last 6h</option>
              <option value="12h">Last 12h</option>
              <option value="24h">Last 24h</option>
            </select>
          </div>
        </div>

        <div className="mt-3 flex justify-end">
          <button
            onClick={loadTimeseries}
            disabled={!serial || !metric || tsLoading || filteredMetrics.length === 0}
            className="rounded-xl bg-black text-white px-4 py-2 disabled:opacity-60"
          >
            {tsLoading ? 'Loading...' : 'Load Chart'}
          </button>
        </div>

        {tsError && <div className="mt-3 rounded-xl border bg-red-50 p-3 text-sm text-red-800">{tsError}</div>}
      </div>

      {tsData && (
        <ChartSVG
          labels={tsData.labels}
          data={tsData.series?.[0]?.data || []}
          thresholds={tsData.thresholds || []}
          unit={tsData.unit}
          title={tsData.title}
        />
      )}
    </div>
  )
}
