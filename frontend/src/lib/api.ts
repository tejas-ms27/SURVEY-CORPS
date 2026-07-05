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

// ── Deep fraud engine (the real 22-detector analysis + court-ready PDF) ──────
export type FraudNarrative = {
  lines: string[]
  total_moved_display: string
  money_into_network_display: string
  primary_source: string
  intermediary_count: number
  fan_out: string
  fan_in: string
  pooled_accounts: string[]
  kingpin: string
  first_target: string
  traced_amount_display: string
  untraced_amount_display: string
}
export type PrimeSuspect = {
  rank: number
  holder: string
  account_number: string
  score: number
  band: string
  key_concern: string
  top_finding: string
}
export type FindingBullet = {
  pattern: string
  text: string
  evidence_strength: string
  count: number
}
export type RankedSuspect = {
  rank: number
  account_id: string
  holder: string
  bank: string
  account_number: string
  score: number
  band: string
  band_label?: string
  strong_pattern_count: number
  distinct_pattern_count: number
  total_findings: number
  overview: string
  bullets: FindingBullet[]
  key_concern: string
}
export type PatternFinding = { accounts: string[]; text: string; evidence_strength: string }
export type ScoredPattern = {
  pattern_id: number
  name: string
  count: number
  priority: boolean
  findings: PatternFinding[]
}
export type AnalysisSummary = {
  accounts_analyzed?: number
  total_transactions?: number
  counterparty_resolution_rate?: number
  accounts_flagged?: number
  graph_nodes?: number
  graph_edges?: number
  balance_note?: string
  llm_status?: string
}
export type CaseReconstruction = {
  summary?: string
  cluster_count?: number
  connected_clusters?: Array<{
    cluster_id: string
    summary: string
    members: string[]
    account_count: number
    edge_count: number
    highest_priority_account: string
    total_score: number
  }>
  isolated_clusters?: Array<{ cluster_id: string; members: string[] }>
}
export type FraudAnalysis = {
  case_narrative: FraudNarrative
  prime_suspects: PrimeSuspect[]
  ranked_accounts: RankedSuspect[]
  ranked_shown: number
  ranked_total: number
  analysis_summary: AnalysisSummary
  case_reconstruction: CaseReconstruction
  final_summary: { ranked_table: Array<{ rank: number; account: string; score: number; key_concern: string }> }
  data_security: { local_items: string[]; external_items: string[]; llm_status: string; llm_call_count: number }
  scored_patterns: ScoredPattern[]
  leads: ScoredPattern[]
}
export type JobStatus = { status: 'not_run' | 'running' | 'done' | 'error'; error?: string; format?: string; language?: string }

// ── Interactive investigation graphs (served from analysis run's ui_graphs) ──
export type MoneyFlowNode = {
  id: string
  label?: string
  account_number?: string
  holder?: string
  cluster_id?: string
  observed_account?: boolean
  pattern_count?: number
  reconstruction_degree?: number
  total_score?: number
  suspicion_tiers?: unknown
}
export type MoneyFlowEdge = {
  id?: string
  source: string
  target: string
  amount?: number
  date?: string
  txn_ids?: string[]
  confidence_score?: number
  pattern_supported?: boolean
  included_in_case_reconstruction?: boolean
  reconstruction_reason?: string
  high_degree_public_endpoint?: boolean
}
export type MoneyFlowGraphData = {
  type: string
  labels?: Record<string, string>
  data: {
    nodes: MoneyFlowNode[]
    edges: MoneyFlowEdge[]
    clusters?: Array<Record<string, unknown>>
    scope?: string
    raw_filtered_node_count?: number
    raw_filtered_edge_count?: number
  }
}
export type SourceCreditDetails = {
  date?: string
  time?: string
  narration?: string
  reference?: string
  txn_type?: string
  sender?: string
  is_observed_account?: boolean
}
export type TrailAllocation = {
  date?: string
  debit_amount?: number
  allocated_from_credit?: number
  balance_after_debit?: number
  counterparty_account?: string
  counterparty_name_raw?: string
  debit_txn_id?: string
  narration?: string
  txn_type?: string
}
export type MoneyTrail = {
  finding_id?: string
  accounts?: string[]
  source_credit_txn_id?: string
  credited_amount?: number
  trace_status?: string
  allocations?: TrailAllocation[]
  source_credit_details?: SourceCreditDetails
}
/** A single incoming credit in the Level-2 list (summary only — no FIFO trace yet). */
export type MoneyTrailCredit = {
  txn_id: string
  credited_amount?: number
  date?: string
  time?: string
  narration?: string
  reference?: string
  txn_type?: string
  sender?: string
  is_observed_account?: boolean
}
/** One uploaded account and its incoming credits, sorted highest→lowest. */
export type MoneyTrailAccount = {
  account_id: string
  label?: string
  account_number?: string
  holder?: string
  credit_count: number
  total_credited: number
  credits: MoneyTrailCredit[]
}
export type MoneyTrailGraphData = {
  type: string
  labels?: Record<string, string>
  accounts: MoneyTrailAccount[]
}

export type BalancePoint = { date?: string; txn_id?: string; balance?: number | null; net_amount?: number }
export type BalanceAccount = { account_id: string; points: BalancePoint[] }
export type BalanceGraphData = { type: string; labels?: Record<string, string>; accounts: BalanceAccount[] }

export type SankeyNode = { label: string; kind: 'account' | 'bucket' | 'external' }
export type SankeyLink = { source: number; target: number; value: number }
export type SankeyGraphData = {
  type: string
  nodes: SankeyNode[]
  links: SankeyLink[]
}
export type FullFlowNode = {
  id: string
  label: string
  kind: 'observed' | 'person' | 'upi' | 'account' | 'charge' | 'unknown' | 'other'
  total_volume: number
  txn_count: number
}
export type FullFlowEdge = {
  source: string
  target: string
  amount: number
  txn_count: number
  first_date: string
  last_date: string
  txn_type: string
  sample_narration: string
}
export type FullFlowAccount = { id: string; label: string; txn_count: number }
export type FullFlowGraphData = {
  type: string
  total_transactions: number
  resolved_transactions: number
  accounts: FullFlowAccount[]
  nodes: FullFlowNode[]
  edges: FullFlowEdge[]
}

export type GraphsAvailable = { case_id: string; available: Record<string, boolean> }

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

  // Deep fraud engine (real 22 detectors + suspicion scores + Case Narrative + PDF)
  runFraud: (caseId: string) =>
    request<JobStatus>(`/api/cases/${encodeURIComponent(caseId)}/fraud/run`, { method: 'POST' }),
  fraudStatus: (caseId: string) =>
    request<JobStatus>(`/api/cases/${encodeURIComponent(caseId)}/fraud/status`),
  getFraud: (caseId: string) => request<FraudAnalysis>(`/api/cases/${encodeURIComponent(caseId)}/fraud`),
  listGraphs: (caseId: string) =>
    request<GraphsAvailable>(`/api/cases/${encodeURIComponent(caseId)}/fraud/graphs`),
  getMoneyFlowGraph: (caseId: string) =>
    request<MoneyFlowGraphData>(`/api/cases/${encodeURIComponent(caseId)}/fraud/graphs/money_flow`),
  getMoneyTrailGraph: (caseId: string) =>
    request<MoneyTrailGraphData>(`/api/cases/${encodeURIComponent(caseId)}/fraud/graphs/money_trail`),
  // Lazily trace ONE selected credit's FIFO money trail (Level 3). Kept separate from the
  // index so the credit list loads instantly even for cases with tens of thousands of credits.
  getMoneyTrail: (caseId: string, txnId: string) =>
    request<MoneyTrail>(`/api/cases/${encodeURIComponent(caseId)}/fraud/graphs/money_trail/credit/${encodeURIComponent(txnId)}`),
  // Absolute URL for the Money Trail → Word (.docx) export of one credit's trail,
  // rendered in the ORIGINAL statement layout. Fetched as a blob by the download button.
  moneyTrailDocxUrl: (caseId: string, txnId: string) =>
    `${BASE_URL}/api/cases/${encodeURIComponent(caseId)}/fraud/graphs/money_trail/credit/${encodeURIComponent(txnId)}/docx`,
  getBalanceGraph: (caseId: string) =>
    request<BalanceGraphData>(`/api/cases/${encodeURIComponent(caseId)}/fraud/graphs/balance`),
  getSankeyGraph: (caseId: string) =>
    request<SankeyGraphData>(`/api/cases/${encodeURIComponent(caseId)}/fraud/graphs/sankey`),
  getFullFlowGraph: (caseId: string) =>
    request<FullFlowGraphData>(`/api/cases/${encodeURIComponent(caseId)}/fraud/graphs/all_flows`),
  runReportPdf: (caseId: string, language: 'en' | 'kn' = 'en') =>
    request<JobStatus>(`/api/cases/${encodeURIComponent(caseId)}/fraud/report/run?language=${language}`, {
      method: 'POST',
    }),
  reportPdfStatus: (caseId: string, language: 'en' | 'kn' = 'en') =>
    request<JobStatus>(`/api/cases/${encodeURIComponent(caseId)}/fraud/report/status?language=${language}`),
  reportPdfUrl: (caseId: string, language: 'en' | 'kn' = 'en') =>
    `${BASE_URL}/api/cases/${encodeURIComponent(caseId)}/fraud/report/download?language=${language}`,

  reportHtml: (caseId: string) => request<string>(`/api/cases/${encodeURIComponent(caseId)}/report`),
  reportDownloads: (caseId: string) =>
    request<{ available: Record<string, string> }>(`/api/cases/${encodeURIComponent(caseId)}/report/downloads`),
  downloadUrl: (caseId: string, key: string) =>
    `${BASE_URL}/api/cases/${encodeURIComponent(caseId)}/report/downloads/${key}`,
}

export { ApiError, BASE_URL }
