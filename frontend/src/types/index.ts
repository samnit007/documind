export interface Citation {
  source: string
  section: string
  url: string | null
  excerpt: string
}

export interface RAGResponse {
  answer: string
  citations: Citation[]
  confidence: number
  sources_used: string[]
  token_cost_usd: number
}

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  response?: RAGResponse
  loading?: boolean
  error?: string
}

export type Provider = 'claude' | 'openai'
