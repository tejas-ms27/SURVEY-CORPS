import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { SectionHeader } from '@/components/common/SectionHeader'
import { MetricCard } from '@/components/common/MetricCard'
import { DataTable } from '@/components/common/DataTable'
import { SimpleBarChart } from '@/components/analysis/SimpleBarChart'
import { RelationshipGraph } from '@/components/analysis/RelationshipGraph'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  api,
  type AccountRow,
  type CaseSummary,
  type CounterpartyRow,
  type DuplicateRow,
  type FlagRow,
  type GraphResponse,
} from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

export function Analysis() {
  const navigate = useNavigate()
  const activeCaseId = useAppStore((s) => s.activeCaseId)

  const [summary, setSummary] = useState<CaseSummary | null>(null)
  const [accounts, setAccounts] = useState<AccountRow[]>([])
  const [flags, setFlags] = useState<FlagRow[]>([])
  const [duplicates, setDuplicates] = useState<DuplicateRow[]>([])
  const [counterparties, setCounterparties] = useState<CounterpartyRow[]>([])
  const [graph, setGraph] = useState<GraphResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!activeCaseId) {
      setLoading(false)
      return
    }
    setLoading(true)
    Promise.all([
      api.getCaseSummary(activeCaseId),
      api.getAccounts(activeCaseId),
      api.getFlags(activeCaseId),
      api.getDuplicates(activeCaseId),
      api.getCounterparties(activeCaseId),
      api.getGraph(activeCaseId),
    ]).then(([s, a, f, d, c, g]) => {
      setSummary(s)
      setAccounts(a.accounts)
      setFlags(f.flags)
      setDuplicates(d.duplicates)
      setCounterparties(c.counterparties)
      setGraph(g)
      setLoading(false)
    })
  }, [activeCaseId])

  if (!activeCaseId) {
    return (
      <div>
        <SectionHeader eyebrow="Read the case" title="Analysis" />
        <Card className="px-4 py-6 text-sm text-muted-foreground">
          Run extraction first, or pick an existing case from the sidebar.
        </Card>
      </div>
    )
  }

  return (
    <div>
      <SectionHeader
        eyebrow="Read the case"
        title="Analysis"
        sub="Reconciled ledgers, flags, duplicates and money movement for the active case."
      />

      {loading || !summary ? (
        <p className="text-sm text-muted-foreground">Loading case…</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetricCard label="Accounts" value={summary.accounts} />
            <MetricCard label="Clean rows" value={summary.clean_rows} />
            <MetricCard label="Flagged rows" value={summary.flagged_rows} />
            <MetricCard label="Indexed chunks" value={summary.indexed_chunks} />
          </div>
          <p className="mt-2 truncate font-mono text-xs text-faint">Case path: {summary.case_dir}</p>

          <h2 className="mt-8 mb-2 text-sm font-bold text-ink">Per-account summary</h2>
          <DataTable
            columns={[
              { key: 'holder', label: 'Holder' },
              { key: 'bank', label: 'Bank' },
              { key: 'account', label: 'Account', mono: true },
              { key: 'statement_period', label: 'Period' },
              { key: 'opening_balance', label: 'Opening', mono: true, align: 'right' },
              { key: 'closing_balance', label: 'Closing', mono: true, align: 'right' },
              { key: 'transactions', label: 'Txns', align: 'right' },
              { key: 'flagged', label: 'Flagged', align: 'right' },
            ]}
            rows={accounts}
            empty="No accounts found."
          />

          <div className="mt-8 grid gap-5 lg:grid-cols-2">
            <div>
              <h2 className="mb-2 text-sm font-bold text-ink">Flag reason breakdown</h2>
              {flags.length === 0 ? (
                <Card className="px-4 py-6 text-center text-sm text-muted-foreground">No flagged transactions.</Card>
              ) : (
                <Card className="p-4">
                  <SimpleBarChart data={flags} xKey="flag_reason" yKey="count" color="#cf2727" />
                </Card>
              )}
            </div>
            <div>
              <h2 className="mb-2 text-sm font-bold text-ink">Duplicate summary</h2>
              {duplicates.length === 0 ? (
                <Card className="px-4 py-6 text-center text-sm text-muted-foreground">No duplicate transactions.</Card>
              ) : (
                <Card className="p-4">
                  <SimpleBarChart data={duplicates} xKey="account_number" yKey="duplicates" color="#ebebeb" />
                </Card>
              )}
            </div>
          </div>

          <h2 className="mt-8 mb-2 text-sm font-bold text-ink">Top counterparties (approximate)</h2>
          <DataTable
            columns={[
              { key: 'counterparty', label: 'Counterparty' },
              {
                key: 'inflow',
                label: 'Inflow',
                align: 'right',
                mono: true,
                render: (r) => `Rs. ${r.inflow.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
              },
              {
                key: 'outflow',
                label: 'Outflow',
                align: 'right',
                mono: true,
                render: (r) => `Rs. ${r.outflow.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
              },
              { key: 'txns', label: 'Txns', align: 'right' },
            ]}
            rows={counterparties}
            empty="No clean counterparty hints found in narrations."
          />

          <h2 className="mt-8 mb-2 text-sm font-bold text-ink">Approximate counterparty graph</h2>
          <p className="mb-2 text-xs text-muted-foreground">
            Counterparty nodes are derived from transaction narration text and are approximate — likely external
            parties from free-text descriptions, not verified account matches.
          </p>
          {graph && <RelationshipGraph graph={graph} />}

          <div className="mt-8 flex items-center justify-between border-t border-line pt-5">
            <p className="text-sm text-muted-foreground">Reviewed the case? Open the investigator chatbot to interrogate it.</p>
            <Button onClick={() => navigate('/chatbot')}>Proceed to chatbot →</Button>
          </div>
        </>
      )}
    </div>
  )
}
