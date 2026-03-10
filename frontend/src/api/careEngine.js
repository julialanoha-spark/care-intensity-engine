const BASE = '/api'

export async function fetchConditions() {
  const res = await fetch(`${BASE}/conditions/`)
  if (!res.ok) throw new Error('Failed to load conditions')
  return res.json()
}

export async function fetchProviders() {
  const res = await fetch(`${BASE}/providers/`)
  if (!res.ok) throw new Error('Failed to load providers')
  return res.json()
}

export async function fetchMedications() {
  const res = await fetch(`${BASE}/medications/`)
  if (!res.ok) throw new Error('Failed to load medications')
  return res.json()
}

export async function postScore(payload) {
  const res = await fetch(`${BASE}/score/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Scoring request failed')
  return res.json()
}
