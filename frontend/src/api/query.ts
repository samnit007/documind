import type { RAGResponse, Provider } from '../types'

const BASE = (import.meta.env.VITE_API_URL ?? '') + '/api'

export async function askQuestion(question: string, provider: Provider): Promise<RAGResponse> {
  const res = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, provider }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail ?? 'Request failed')
  }
  return res.json()
}

export async function getHealth(): Promise<{ status: string; chunks_indexed: number }> {
  const res = await fetch(`${BASE}/health`)
  return res.json()
}
