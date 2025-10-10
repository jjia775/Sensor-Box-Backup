import { useMemo, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'

export default function Login() {
  const navigate = useNavigate()
  const API_BASE = useMemo(() => import.meta.env.VITE_API_BASE || 'http://localhost:8000', [])
  const [value, setValue] = useState('')

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed) return
    // 这里把“Household”当成你的 House ID 使用
    localStorage.setItem('house_id', trimmed)
    navigate(`/dashboard/${encodeURIComponent(trimmed)}`)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto w-full max-w-md bg-white rounded-2xl shadow p-6">
        <h1 className="text-2xl font-bold mb-4">Login</h1>
        <p className="text-sm text-gray-600 mb-4">
          输入你的 <span className="font-semibold">Household（House&nbsp;ID）</span> 以进入对应的 Dashboard。
        </p>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Household / House ID</label>
            <input
              className="w-full rounded-xl border px-3 py-2"
              placeholder="例如：C-DOE-1234"
              value={value}
              onChange={e => setValue(e.target.value)}
              required
              autoFocus
            />
          </div>
          <button
            type="submit"
            className="w-full rounded-xl bg-black text-white py-2 font-semibold"
          >
            Go to Dashboard
          </button>
        </form>

        <div className="mt-6 flex items-center justify-between">
          <div className="text-xs text-gray-500">API: {API_BASE}</div>
          <Link
            to="/register"
            className="text-sm rounded-xl border px-3 py-1 hover:bg-gray-100"
          >
            Go to Register
          </Link>
        </div>
      </div>
    </div>
  )
}
