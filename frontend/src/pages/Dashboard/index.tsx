import { useEffect, useMemo, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useApiBase } from '../../hooks/useApiBase'
import SensorGrid from '../../components/SensorGrid'
import ChartsPanel from '../../components/Chart/ChartsPanel'
import type { Sensor } from '../../types/sensors'

type Disease = {
  key: string
  name: string
  metrics: string[]
}

export default function Dashboard() {
  const { houseId } = useParams()
  const API_BASE = useApiBase()

  const [tab, setTab] = useState<'sensors' | 'charts'>('sensors')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [items, setItems] = useState<Sensor[]>([])

  // 疾病列表与当前选择
  const [diseases, setDiseases] = useState<Disease[]>([])
  const [selectedDiseaseKey, setSelectedDiseaseKey] = useState<string>('')

  const hid = houseId || localStorage.getItem('house_id') || ''

  // 拉取住户下的传感器
  useEffect(() => {
    if (!hid) {
      setError('Missing house_id')
      setLoading(false)
      return
    }
    localStorage.setItem('house_id', hid)
    const url = `${API_BASE}/sensors/?house_id=${encodeURIComponent(hid)}`
    fetch(url)
      .then(async r => {
        if (!r.ok) throw new Error(await r.text())
        return r.json()
      })
      .then((data: Sensor[]) => setItems(data))
      .catch(e => setError(e?.message || 'Failed to load sensors'))
      .finally(() => setLoading(false))
  }, [hid, API_BASE])

  // 拉取疾病列表（进入 charts 前需要）
  useEffect(() => {
    let alive = true
    fetch(`${API_BASE}/api/diseases/`)
      .then(async r => {
        if (!r.ok) throw new Error(await r.text())
        return r.json()
      })
      .then((data) => {
        if (!alive) return
        const list: Disease[] = data?.diseases ?? []
        setDiseases(list)
        // 恢复上次选择或默认第一个
        const saved = localStorage.getItem('disease_key') || ''
        const initKey = list.find(d => d.key === saved)?.key || list[0]?.key || ''
        setSelectedDiseaseKey(initKey)
      })
      .catch(() => setDiseases([]))
    return () => { alive = false }
  }, [API_BASE])

  const selectedDisease = useMemo(
    () => diseases.find(d => d.key === selectedDiseaseKey),
    [diseases, selectedDiseaseKey]
  )

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-6xl">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <div className="flex gap-2">
            <button
              onClick={() => setTab('sensors')}
              className={`rounded-xl px-4 py-2 border ${tab === 'sensors' ? 'bg-black text-white' : 'hover:bg-gray-100'}`}
            >
              Sensors
            </button>
            <button
              onClick={() => setTab('charts')}
              className={`rounded-xl px-4 py-2 border ${tab === 'charts' ? 'bg-black text-white' : 'hover:bg-gray-100'}`}
            >
              Charts
            </button>
            <Link to="/register" className="rounded-xl border px-4 py-2 hover:bg-gray-100">New Register</Link>
          </div>
        </div>

        <div className="mb-4 text-sm text-gray-600">API: {API_BASE}</div>

        {tab === 'sensors' && (
          <>
            {loading && <div className="text-gray-600">Loading...</div>}
            {error && (
              <div className="rounded-xl border bg-red-50 p-4 text-red-800 mb-4">
                <div className="font-semibold">Error</div>
                <div className="text-sm whitespace-pre-wrap">{error}</div>
              </div>
            )}
            {!loading && !error && <SensorGrid items={items} />}
          </>
        )}

        {tab === 'charts' && (
          <>
            {!hid && (
              <div className="rounded-xl border bg-yellow-50 p-4 text-yellow-800">
                Missing house_id. Please login again.
              </div>
            )}

            {hid && (
              <div className="space-y-4">
                {/* 疾病选择器 */}
                <div className="rounded-2xl bg-white border shadow p-4">
                  <div className="mb-2 text-gray-800 font-semibold">选择疾病</div>
                  <div className="flex flex-wrap gap-3">
                    {diseases.map(d => (
                      <button
                        key={d.key}
                        onClick={() => {
                          setSelectedDiseaseKey(d.key)
                          localStorage.setItem('disease_key', d.key)
                        }}
                        className={`px-3 py-1 rounded-full border text-sm ${
                          selectedDiseaseKey === d.key
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'hover:bg-gray-100'
                        }`}
                      >
                        {d.name}
                      </button>
                    ))}
                    {(!diseases || diseases.length === 0) && (
                      <span className="text-gray-500 text-sm">无疾病配置</span>
                    )}
                  </div>
                </div>

                {/* Chart 面板（受疾病 metrics 限制） */}
                {selectedDisease ? (
                  <ChartsPanel
                    apiBase={API_BASE}
                    houseId={hid}
                    allowedMetrics={selectedDisease.metrics}
                  />
                ) : (
                  <div className="rounded-xl border bg-amber-50 p-4 text-amber-800">
                    请先在上方选择疾病，然后查看图表。
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
