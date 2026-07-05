import { useEffect, useState, type ReactNode } from 'react'
import { Loader2, Network, Route, LineChart as LineChartIcon, GitFork, Globe } from 'lucide-react'

import { Card } from '@/components/ui/card'
import { MoneyFlowGraph } from '@/components/workflow/MoneyFlowGraph'
import { MoneyTrailGraph } from '@/components/workflow/MoneyTrailGraph'
import { BalanceGraph } from '@/components/workflow/BalanceGraph'
import { SankeyGraph } from '@/components/workflow/SankeyGraph'
import { FullFlowGraph } from '@/components/workflow/FullFlowGraph'
import { api, ApiError } from '@/lib/api'

/* Relationships stage → the investigation graph dashboard. Every graph is rendered
 * from the analysis run's ui_graphs JSON (SQL stays the source of truth; these are
 * read-only projections). Tabs lazy-load their data so large cases stay responsive. */

type TabKey = 'money_flow' | 'money_trail' | 'balance' | 'sankey' | 'full_flow'

const TABS: { key: TabKey; label: string; icon: ReactNode; blurb: string }[] = [
  { key: 'money_flow', label: 'Money Flow', icon: <Network className="size-4" />, blurb: 'Reconstruction-included evidence edges between accounts. Click to isolate neighbours; hover for the underlying facts.' },
  { key: 'full_flow', label: 'Full Flow', icon: <Globe className="size-4" />, blurb: 'Complete knowledge graph of all resolved transactions — every account and every counterparty visible. Use the amount filter to reduce clutter. Red = your accounts, orange = UPI, blue = bank account numbers.' },
  { key: 'money_trail', label: 'Money Trail', icon: <Route className="size-4" />, blurb: 'Pick an account, then any incoming credit (highest→lowest) to replay where those funds came from and how they were distributed across subsequent debits (FIFO tracing), transaction-by-transaction in chronological order.' },
  { key: 'balance', label: 'Balance', icon: <LineChartIcon className="size-4" />, blurb: 'Balance evolution over time. Toggle accounts to compare how their balances move.' },
  { key: 'sankey', label: 'Sankey', icon: <GitFork className="size-4" />, blurb: 'Money flow by transaction type (UPI / NEFT / RTGS / Cash / IMPS). Link width is proportional to the amount moved.' },
]

/** Fetches one graph's JSON on mount and renders it via `children`. */
function GraphLoader<T>({ caseId, fetcher, isEmpty, children }: {
  caseId: string
  fetcher: (caseId: string) => Promise<T>
  isEmpty: (data: T) => boolean
  children: (data: T) => ReactNode
}) {
  const [data, setData] = useState<T | null>(null)
  const [state, setState] = useState<'loading' | 'ready' | 'empty' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!caseId) return setState('empty')
    let cancelled = false
    setState('loading')
    fetcher(caseId)
      .then((d) => {
        if (cancelled) return
        setData(d)
        setState(isEmpty(d) ? 'empty' : 'ready')
      })
      .catch((err) => {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 404) {
          setState('empty')
          setMessage('This graph was not generated for this case.')
        } else {
          setState('error')
          setMessage(err instanceof Error ? err.message : 'Could not load the graph.')
        }
      })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId])

  if (state === 'loading')
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-24 text-center">
        <Loader2 className="size-6 animate-spin text-teal" />
        <p className="text-sm text-muted-foreground">Loading the investigation graph…</p>
      </div>
    )
  if (state === 'error') return <div className="py-20 text-center text-sm text-[#cf2727]">{message}</div>
  if (state === 'empty') return <div className="py-20 text-center text-sm text-muted-foreground">{message || 'Nothing to display for this graph.'}</div>
  return <>{data && children(data)}</>
}

export function GraphPreview({ caseId }: { caseId: string }) {
  const [tab, setTab] = useState<TabKey>('money_flow')
  const active = TABS.find((t) => t.key === tab)!

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-1.5">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-semibold transition-colors ${
              tab === t.key ? 'border-teal bg-teal/15 text-ink' : 'border-line text-muted-foreground hover:text-ink'
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      <div>
        <h2 className="text-sm font-bold text-ink">{active.label} graph</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">{active.blurb} Every element traces back to a real transaction.</p>
      </div>

      <Card className="p-4">
        {tab === 'money_flow' && (
          <GraphLoader caseId={caseId} fetcher={api.getMoneyFlowGraph} isEmpty={(d) => (d.data?.nodes?.length ?? 0) === 0}>
            {(d) => <MoneyFlowGraph graph={d} />}
          </GraphLoader>
        )}
        {tab === 'money_trail' && (
          <GraphLoader caseId={caseId} fetcher={api.getMoneyTrailGraph} isEmpty={(d) => (d.accounts?.length ?? 0) === 0}>
            {(d) => <MoneyTrailGraph graph={d} caseId={caseId} />}
          </GraphLoader>
        )}
        {tab === 'balance' && (
          <GraphLoader caseId={caseId} fetcher={api.getBalanceGraph} isEmpty={(d) => (d.accounts?.length ?? 0) === 0}>
            {(d) => <BalanceGraph graph={d} />}
          </GraphLoader>
        )}
        {tab === 'sankey' && (
          <GraphLoader caseId={caseId} fetcher={api.getSankeyGraph} isEmpty={(d) => (d.links?.length ?? 0) === 0}>
            {(d) => <SankeyGraph graph={d} />}
          </GraphLoader>
        )}
        {tab === 'full_flow' && (
          <GraphLoader caseId={caseId} fetcher={api.getFullFlowGraph} isEmpty={(d) => (d.nodes?.length ?? 0) === 0}>
            {(d) => <FullFlowGraph graph={d} />}
          </GraphLoader>
        )}
      </Card>
    </div>
  )
}
