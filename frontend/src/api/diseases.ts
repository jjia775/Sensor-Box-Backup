// src/api/diseases.ts
export type Disease = {
  key: string
  name: string
  metrics: string[]
}

export async function fetchDiseases(apiBase: string): Promise<Disease[]> {
  const r = await fetch(`${apiBase}/api/diseases/`)
  if (!r.ok) throw new Error(await r.text())
  const data = await r.json()
  return data?.diseases ?? []
}

export async function fetchDisease(apiBase: string, key: string): Promise<Disease> {
  const r = await fetch(`${apiBase}/api/diseases/${encodeURIComponent(key)}`)
  if (!r.ok) throw new Error(await r.text())
  return await r.json()
}
