const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: init?.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail)
  }
  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) return res.json()
  return res.text() as unknown as T
}

export type CaseListResponse = { cases: string[]; latest: string | null }
export type CaseSummary = {
  case_id: string
  case_dir: string
  accounts: number
  clean_rows: number
  flagged_rows: number
  indexed_chunks: number
}

export type AccountRow = {
  holder: string
  bank: string
  account: string
  statement_period: string
  opening_balance: string
  closing_balance: string
  transactions: number
  flagged: number
}

export type FlagRow = { flag_reason: string; count: number }
export type DuplicateRow = { account_number: string; duplicates: number }
export type CounterpartyRow = {
  counterparty: string
  inflow: number
  outflow: number
  txns: number
  total: number
}

export type GraphNode = { id: string; label: string; type: 'account' | 'counterparty' }
export type GraphEdge = { source: string; target: string; weight: number; count: number }
export type GraphResponse = { nodes: GraphNode[]; edges: GraphEdge[] }

export type TransactionRow = Record<string, unknown>
export type TransactionsResponse = {
  total: number
  offset: number
  limit: number
  rows: TransactionRow[]
}

export type ExtractionResult = {
  session_id: string
  elapsed_seconds: number
  elapsed_label: string
  clean_rows: number
  flagged_rows: number
  files_processed: number
  files_failed: string[]
  per_file: Record<string, unknown>[]
  clean_preview: TransactionRow[]
  flagged_preview: TransactionRow[]
  downloads_available: string[]
  indexed_chunks: number
}

export type ChatResponse = {
  answer: string
  citations: Record<string, unknown>[]
  matched_pattern: string
  detected_language: string
  structuring_alerts: string[]
  graph_html: string | null
  disclaimer: string | null
  chart: Record<string, unknown> | null
}

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
  ts?: number
  meta?: string
  citations?: Record<string, unknown>[]
  structuring_alerts?: string[]
  graph_html?: string | null
  disclaimer?: string | null
  chart?: Record<string, unknown> | null
}

export const api = {
  listCases: () => request<CaseListResponse>('/api/cases'),
  getCaseSummary: (caseId: string) => request<CaseSummary>(`/api/cases/${encodeURIComponent(caseId)}/summary`),
  deleteCase: (caseId: string) =>
    request<{ ok: boolean; message: string; next_active: string | null }>(
      `/api/cases/${encodeURIComponent(caseId)}`,
      { method: 'DELETE' },
    ),
  reindexCase: (caseId: string) =>
    request<{ case_id: string; indexed_chunks: number }>(`/api/cases/${encodeURIComponent(caseId)}/reindex`, {
      method: 'POST',
    }),

  runExtraction: (form: FormData) =>
    request<ExtractionResult>('/api/extraction/run', { method: 'POST', body: form }),

  getAccounts: (caseId: string) =>
    request<{ accounts: AccountRow[] }>(`/api/cases/${encodeURIComponent(caseId)}/accounts`),
  getFlags: (caseId: string) => request<{ flags: FlagRow[] }>(`/api/cases/${encodeURIComponent(caseId)}/flags`),
  getDuplicates: (caseId: string) =>
    request<{ duplicates: DuplicateRow[] }>(`/api/cases/${encodeURIComponent(caseId)}/duplicates`),
  getCounterparties: (caseId: string) =>
    request<{ counterparties: CounterpartyRow[] }>(`/api/cases/${encodeURIComponent(caseId)}/counterparties`),
  getGraph: (caseId: string) => request<GraphResponse>(`/api/cases/${encodeURIComponent(caseId)}/graph`),
  getTransactions: (caseId: string, params: { source?: string; account?: string; limit?: number; offset?: number }) => {
    const search = new URLSearchParams()
    if (params.source) search.set('source', params.source)
    if (params.account) search.set('account', params.account)
    if (params.limit) search.set('limit', String(params.limit))
    if (params.offset) search.set('offset', String(params.offset))
    return request<TransactionsResponse>(`/api/cases/${encodeURIComponent(caseId)}/transactions?${search}`)
  },

  chatStatus: (caseId: string) =>
    request<{ groq_configured: boolean }>(`/api/cases/${encodeURIComponent(caseId)}/chat/status`),
  chatHistory: (caseId: string) =>
    request<{ messages: ChatMessage[] }>(`/api/cases/${encodeURIComponent(caseId)}/chat/history`),
  askQuestion: (caseId: string, question: string) =>
    request<ChatResponse>(`/api/cases/${encodeURIComponent(caseId)}/chat`, {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  reportHtml: (caseId: string) => request<string>(`/api/cases/${encodeURIComponent(caseId)}/report`),
  reportDownloads: (caseId: string) =>
    request<{ available: Record<string, string> }>(`/api/cases/${encodeURIComponent(caseId)}/report/downloads`),
  downloadUrl: (caseId: string, key: string) =>
    `${BASE_URL}/api/cases/${encodeURIComponent(caseId)}/report/downloads/${key}`,
}

export { ApiError, BASE_URL }
