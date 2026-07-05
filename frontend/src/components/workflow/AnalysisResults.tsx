import { MetricCard } from '@/components/common/MetricCard'
import { DataTable } from '@/components/common/DataTable'
import { Accordion } from '@/components/common/Accordion'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { FraudAnalysis, ScoredPattern } from '@/lib/api'

function bandBadge(band: string) {
  const b = (band || '').toLowerCase()
  const cls = b === 'strong' ? 'bg-[#cf2727] text-white' : b === 'moderate' ? 'bg-[#d89a20] text-white' : 'bg-line text-ink'
  return <span className={`rounded px-2 py-0.5 text-[0.68rem] font-semibold ${cls}`}>{band}</span>
}

function strengthBadge(s: string) {
  const strong = (s || '').toLowerCase() === 'strong'
  return (
    <Badge variant={strong ? 'default' : 'outline'} className={strong ? 'bg-teal text-white' : ''}>
      {s || 'weak'}
    </Badge>
  )
}

function PatternSection({ title, patterns }: { title: string; patterns: ScoredPattern[] }) {
  if (patterns.length === 0) return null
  return (
    <div>
      <h3 className="mb-2 text-sm font-bold text-ink">{title}</h3>
      <div className="space-y-2">
        {patterns.map((p) => (
          <Accordion
            key={p.pattern_id}
            accent={p.priority}
            defaultOpen={p.priority}
            title={p.name}
            right={<span className="rounded-full bg-line px-2 py-0.5 text-[0.68rem] font-semibold text-ink">{p.count}</span>}
          >
            <ul className="space-y-2.5">
              {p.findings.map((f, i) => (
                <li key={i} className="text-sm text-ink">
                  <div className="mb-0.5 flex flex-wrap items-center gap-2">
                    <span className="font-semibold">{f.accounts.join(' · ') || '—'}</span>
                    {strengthBadge(f.evidence_strength)}
                  </div>
                  <p className="text-[0.82rem] text-muted-foreground">{f.text}</p>
                </li>
              ))}
              {p.count > p.findings.length && (
                <li className="text-xs text-faint">+ {p.count - p.findings.length} more finding(s)</li>
              )}
            </ul>
          </Accordion>
        ))}
      </div>
    </div>
  )
}

export function AnalysisResults({ fraud }: { fraud: FraudAnalysis }) {
  const s = fraud.analysis_summary
  const recon = fraud.case_reconstruction || {}
  const connected = recon.connected_clusters || []
  const isolated = recon.isolated_clusters || []
  const priority = fraud.scored_patterns.filter((p) => p.priority)
  const rest = fraud.scored_patterns.filter((p) => !p.priority)

  return (
    <div className="space-y-6">
      {/* Summarised narration — detailed yet crisp */}
      <Card className="border-l-2 border-l-teal border-line p-4">
        <h2 className="text-sm font-bold text-ink">What the analysis found</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink">
          {fraud.case_narrative.lines.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      </Card>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricCard label="Transactions" value={(s.total_transactions ?? 0).toLocaleString('en-IN')} />
        <MetricCard label="Accounts" value={s.accounts_analyzed ?? 0} />
        <MetricCard label="Counterparties resolved" value={`${(s.counterparty_resolution_rate ?? 0).toFixed(0)}%`} />
        <MetricCard label="LLM status" value={s.llm_status || '—'} />
        <MetricCard label="Clusters" value={recon.cluster_count ?? connected.length + isolated.length} />
        <MetricCard label="Connected clusters" value={connected.length} />
        <MetricCard label="Isolated accounts" value={isolated.length} />
        <MetricCard label="Accounts flagged" value={s.accounts_flagged ?? 0} />
      </div>

      {/* Prime suspects */}
      {fraud.prime_suspects.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-bold text-ink">Prime suspects — investigate first</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {fraud.prime_suspects.map((p) => (
              <Card key={p.rank} className="p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-bold text-ink">#{p.rank} · {p.holder}</span>
                  <span className="flex flex-none items-center gap-1.5">{bandBadge(p.band)}<span className="text-xs font-semibold text-ink">{p.score.toLocaleString('en-IN')}</span></span>
                </div>
                {p.account_number && <p className="mt-0.5 font-mono text-[0.7rem] text-faint">{p.account_number}</p>}
                <p className="mt-1 text-xs text-muted-foreground">Key concern: {p.key_concern}</p>
                {p.top_finding && <p className="mt-1 text-xs text-ink">{p.top_finding}</p>}
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Case reconstruction */}
      {(recon.summary || connected.length > 0) && (
        <div>
          <h3 className="mb-2 text-sm font-bold text-ink">Case reconstruction</h3>
          {recon.summary && <p className="mb-2 text-sm text-muted-foreground">{recon.summary}</p>}
          <div className="space-y-2">
            {connected.map((c) => (
              <Accordion
                key={c.cluster_id}
                title={`${c.cluster_id} · ${c.account_count} account(s), ${c.edge_count} link(s)`}
                right={<span className="rounded-full bg-line px-2 py-0.5 text-[0.68rem] font-semibold text-ink">score {Math.round(c.total_score)}</span>}
              >
                <p className="text-[0.82rem] text-ink">{c.summary}</p>
                <p className="mt-2 text-xs text-muted-foreground">Investigate first: <span className="text-ink">{c.highest_priority_account || '—'}</span></p>
                <p className="mt-1 text-xs"><span className="font-semibold text-ink">Members:</span> <span className="text-muted-foreground">{c.members.slice(0, 40).join(', ')}</span></p>
              </Accordion>
            ))}
          </div>
        </div>
      )}

      {/* Ranked suspects table */}
      {fraud.ranked_accounts.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-bold text-ink">
            Ranked suspects <span className="text-xs font-normal text-muted-foreground">(top {fraud.ranked_shown} of {fraud.ranked_total})</span>
          </h3>
          <DataTable
            columns={[
              { key: 'rank', label: '#', align: 'right' },
              { key: 'holder', label: 'Account holder' },
              { key: 'account_number', label: 'Account', mono: true },
              { key: 'score', label: 'Score', align: 'right', render: (r) => r.score.toLocaleString('en-IN') },
              { key: 'band', label: 'Risk', render: (r) => bandBadge(r.band_label || r.band) },
              { key: 'strong_pattern_count', label: 'Strong', align: 'right' },
              { key: 'distinct_pattern_count', label: 'Patterns', align: 'right' },
              { key: 'key_concern', label: 'Key concern' },
            ]}
            rows={fraud.ranked_accounts}
            empty="No accounts met the suspicious ranking criteria."
          />
        </div>
      )}

      {/* Findings — priority first, then the rest; zero-finding patterns already excluded */}
      <PatternSection title="Priority findings" patterns={priority} />
      <PatternSection title="Scored patterns" patterns={rest} />

      {/* AI / statistical leads */}
      {fraud.leads.length > 0 && (
        <PatternSection title="AI / statistical leads — verify manually" patterns={fraud.leads} />
      )}
    </div>
  )
}
