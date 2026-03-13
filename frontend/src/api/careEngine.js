const BASE = '/api'

export async function fetchConditions() {
  const res = await fetch(`${BASE}/conditions/`)
  if (!res.ok) throw new Error('Failed to load conditions')
  return res.json()
}

export async function searchProviders(q) {
  if (!q || q.length < 2) return []
  const res = await fetch(`${BASE}/providers/?search=${encodeURIComponent(q)}`)
  if (!res.ok) throw new Error('Failed to search providers')
  return res.json()
}

export async function fetchMedications() {
  const res = await fetch(`${BASE}/medications/`)
  if (!res.ok) throw new Error('Failed to load medications')
  return res.json()
}

export async function searchPlans(q, zip = '') {
  const hasQuery = q && q.length >= 2
  const hasZip   = zip && zip.length === 5
  if (!hasQuery && !hasZip) return []
  const params = new URLSearchParams({ search: q || '' })
  if (hasZip) params.set('zip', zip)
  const res = await fetch(`${BASE}/plans/?${params}`)
  if (!res.ok) throw new Error('Failed to search plans')
  return res.json()
}

export async function postScore(payload, signal) {
  const res = await fetch(`${BASE}/score/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
  if (!res.ok) throw new Error('Scoring request failed')
  return res.json()
}

export async function postReasoning(payload, signal) {
  const res = await fetch(`${BASE}/reasoning/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
  if (!res.ok) throw new Error('Reasoning request failed')
  return res.json()
}
