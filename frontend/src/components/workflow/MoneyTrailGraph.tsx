import { useEffect, useMemo, useRef, useState } from 'react'
import { Pause, Play, SkipBack, SkipForward, ArrowDownLeft, ArrowUpRight, ExternalLink, Search, ChevronRight, Loader2, FileText } from 'lucide-react'

import { api, ApiError } from '@/lib/api'
import type { MoneyTrailGraphData, MoneyTrailAccount, MoneyTrailCredit, MoneyTrail, SourceCreditDetails } from '@/lib/api'

/* Money Trail: replays how a single incoming credit is traced (FIFO) into subsequent
 * debits, in chronological order. Source credit details (sender, type, date, reference)
 * are resolved from analysis.db by the API. All allocation steps carry the real narration,
 * counterparty, amount, and date. Everything traces back to a SQL txn_id. */

// ── helpers ──────────────────────────────────────────────────────────────────

function money(n?: number | null): string {
  if (n == null || !Number.isFinite(n)) return '—'
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 2 })
}

/** Strip SQL "nan" / "None" sentinel strings that the DB emits for NULL. */
function clean(v?: string | null): string {
  if (!v) return ''
  const s = v.trim()
  return /^(nan|none|null|<na>)$/i.test(s) ? '' : s
}

/** Best display label: prefer real identifier over internal source id. */
function labelOf(id: string, labels: Record<string, string>): string {
  if (!id) return '—'
  const mapped = labels[clean(id)] || clean(id)
  return /^(nan|none|null|<na>)$/i.test(mapped) ? id : mapped || id
}

/** Human-friendly trace status. */
function traceStatusLabel(status?: string): { label: string; tip: string } | null {
  if (!status) return null
  switch (status.toLowerCase()) {
    case 'exhausted':
      return { label: 'Fully Traced', tip: 'All credited funds were accounted for through tracked debits.' }
    case 'partially_traced':
      return { label: 'Partially Traced', tip: 'Some credited funds could not be traced to specific debits.' }
    case 'untraced':
      return { label: 'Untraced', tip: 'No debits were matched to this credit.' }
    default:
      return { label: status, tip: '' }
  }
}

const TXN_TYPE_COLORS: Record<string, string> = {
  UPI: '#e8703a',
  NEFT: '#e0559b',
  RTGS: '#7c6cf0',
  IMPS: '#d89a20',
  CHEQUE: '#3f8cff',
  CASH: '#8b5cf6',
  ATM: '#8b5cf6',
  NACH: '#0ea5a3',
  ECS: '#0ea5a3',
  IFT: '#e0559b',
  OTHER: '#9aa0a6',
}

/** The badge shows the mode token VERBATIM (e.g. BLKRTGS, BLKIFT), but its colour is
 *  resolved by the known payment rail contained in the token, so BLKRTGS still reads
 *  RTGS-coloured and BLKNEFT NEFT-coloured — falling back to neutral for anything else. */
function badgeColor(type: string): string {
  const t = type.toUpperCase()
  if (TXN_TYPE_COLORS[t]) return TXN_TYPE_COLORS[t]
  const rail = (['RTGS', 'NEFT', 'IMPS', 'UPI', 'NACH', 'ECS', 'ATM', 'CASH', 'CHEQUE', 'CHQ', 'IFT'] as const).find(
    (r) => t.includes(r),
  )
  return (rail && (TXN_TYPE_COLORS[rail] ?? TXN_TYPE_COLORS[rail === 'CHQ' ? 'CHEQUE' : 'OTHER'])) || TXN_TYPE_COLORS.OTHER
}

function TxnTypeBadge({ type }: { type?: string }) {
  if (!type) return null
  return (
    <span
      className="inline-flex items-center rounded px-1.5 py-0.5 text-[0.6rem] font-bold uppercase tracking-wide text-white"
      style={{ background: badgeColor(type) }}
    >
      {type}
    </span>
  )
}

// ── source credit card ────────────────────────────────────────────────────────

function SourceCreditCard({
  trail,
  labels,
}: {
  trail: MoneyTrail
  labels: Record<string, string>
}) {
  const details: SourceCreditDetails = trail.source_credit_details ?? {}
  const receiverLabel = labelOf(trail.accounts?.[0] ?? '', labels)

  const sender = clean(details.sender)
  const date = clean(details.date)
  const time = clean(details.time)
  const reference = clean(details.reference)
  const narration = clean(details.narration)
  const txnType = details.txn_type || 'Other'

  // Friendly datetime
  const dateStr = date ? (time ? `${date} at ${time}` : date) : ''

  return (
    <div className="rounded-lg border border-[#cf2727]/50 bg-[#cf2727]/10 px-3 py-3 text-sm">
      <div className="flex items-start gap-2">
        <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-[#cf2727] text-[0.65rem] font-bold text-white">
          S
        </span>
        <div className="min-w-0 flex-1 space-y-1">
          {/* Receiver row */}
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
            <span className="font-semibold text-ink">{receiverLabel}</span>
            <span className="text-[#cf2727] font-medium">{money(trail.credited_amount)}</span>
            {dateStr && <span className="text-[0.7rem] text-muted-foreground">{dateStr}</span>}
            <TxnTypeBadge type={txnType} />
          </div>

          {/* Sender row */}
          {sender ? (
            <div className="flex items-center gap-1.5 text-[0.72rem] text-muted-foreground">
              <ArrowDownLeft className="size-3 shrink-0 text-[#cf2727]" />
              <span>Received from </span>
              <span className="font-semibold text-ink">{sender}</span>
              {details.is_observed_account && (
                <span className="rounded bg-amber-500/20 px-1 py-0.5 text-[0.6rem] font-bold text-amber-600">
                  IN INVESTIGATION
                </span>
              )}
              {!details.is_observed_account && (
                <span className="flex items-center gap-0.5 text-faint">
                  <ExternalLink className="size-2.5" />
                  external
                </span>
              )}
            </div>
          ) : (
            <div className="text-[0.72rem] text-faint">Source sender not identified in narration</div>
          )}

          {/* Reference / narration */}
          {reference && (
            <div className="text-[0.65rem] text-faint">
              Ref: <span className="font-mono">{reference}</span>
            </div>
          )}
          {narration && !reference && (
            <div className="truncate text-[0.65rem] text-faint">{narration}</div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── allocation step card ──────────────────────────────────────────────────────

function AllocationCard({
  alloc,
  step,
  active,
  labels,
}: {
  alloc: MoneyTrail['allocations'] extends (infer T)[] | undefined ? T : never
  step: number
  active: boolean
  labels: Record<string, string>
}) {
  if (!alloc) return null

  const cp = clean(alloc.counterparty_account) || clean(alloc.counterparty_name_raw)
  const cpLabel = cp ? labelOf(cp, labels) : '—'
  const narration = clean(alloc.narration)
  const date = clean(alloc.date)

  return (
    <div
      className={`ml-3 flex items-start gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
        active ? 'border-teal/60 bg-teal/10' : 'border-line bg-line-soft/30'
      }`}
    >
      <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-line text-[0.65rem] font-bold text-ink">
        {step}
      </span>
      <div className="min-w-0 flex-1">
        {/* Counterparty + amount + date */}
        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <ArrowUpRight className="size-3 shrink-0 text-muted-foreground" />
          <span className="font-semibold text-ink">{cpLabel}</span>
          <span className="text-[#cf2727]">{money(alloc.debit_amount)}</span>
          {date && <span className="text-[0.7rem] text-faint">{date}</span>}
          <TxnTypeBadge type={alloc.txn_type} />
        </div>

        {/* Narration */}
        {narration && (
          <div className="truncate text-[0.72rem] text-muted-foreground" title={narration}>
            {narration}
          </div>
        )}

        {/* Allocation metadata */}
        <div className="text-[0.65rem] text-faint">
          {money(alloc.allocated_from_credit)} from credit
          {alloc.balance_after_debit != null && ` · balance after: ${money(alloc.balance_after_debit)}`}
        </div>
      </div>
    </div>
  )
}

// ── trail replay ──────────────────────────────────────────────────────────────

function TrailReplay({ trail, labels }: { trail: MoneyTrail; labels: Record<string, string> }) {
  const allocations = useMemo(() => {
    const a = [...(trail.allocations ?? [])]
    a.sort((x, y) => String(x.date ?? '').localeCompare(String(y.date ?? '')))
    return a
  }, [trail])

  const [step, setStep] = useState(0)
  const [playing, setPlaying] = useState(false)
  const timer = useRef<ReturnType<typeof setInterval> | null>(null)
  const total = allocations.length

  useEffect(() => {
    if (!playing) return
    timer.current = setInterval(() => {
      setStep((s) => {
        if (s >= total) { setPlaying(false); return s }
        return s + 1
      })
    }, 900)
    return () => { if (timer.current) clearInterval(timer.current) }
  }, [playing, total])

  const traced = allocations.slice(0, step)
  const statusInfo = traceStatusLabel(trail.trace_status)
  const tracedAmount = traced.reduce((sum, a) => sum + (a.allocated_from_credit ?? 0), 0)

  return (
    <div className="space-y-3">
      {/* Controls bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>
            Tracing <span className="font-semibold text-ink">{money(trail.credited_amount)}</span>
          </span>
          {step > 0 && (
            <span className="text-faint">
              · {money(tracedAmount)} traced so far
            </span>
          )}
          {statusInfo && (
            <span
              className={`rounded px-1.5 py-0.5 text-[0.65rem] font-semibold ${
                trail.trace_status === 'exhausted'
                  ? 'bg-emerald-500/15 text-emerald-700'
                  : 'bg-amber-500/15 text-amber-700'
              }`}
              title={statusInfo.tip}
            >
              {statusInfo.label}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <button
            className="grid size-7 place-items-center rounded-md border border-line text-muted-foreground hover:text-ink disabled:opacity-40"
            onClick={() => { setPlaying(false); setStep(0) }}
            disabled={step === 0}
            aria-label="Restart"
          >
            <SkipBack className="size-3.5" />
          </button>
          <button
            className="grid size-7 place-items-center rounded-md border border-line text-muted-foreground hover:text-ink"
            onClick={() => setPlaying((p) => !p)}
            aria-label={playing ? 'Pause' : 'Play'}
          >
            {playing ? <Pause className="size-3.5" /> : <Play className="size-3.5" />}
          </button>
          <button
            className="grid size-7 place-items-center rounded-md border border-line text-muted-foreground hover:text-ink disabled:opacity-40"
            onClick={() => { setPlaying(false); setStep((s) => Math.min(total, s + 1)) }}
            disabled={step >= total}
            aria-label="Step forward"
          >
            <SkipForward className="size-3.5" />
          </button>
          <span className="ml-1 text-[0.7rem] text-faint">{step}/{total}</span>
        </div>
      </div>

      {/* Scrubber */}
      <input
        type="range"
        min={0}
        max={total}
        value={step}
        onChange={(e) => { setPlaying(false); setStep(Number(e.target.value)) }}
        className="w-full accent-[#cf2727]"
      />

      {/* Transaction list */}
      <div className="max-h-[400px] space-y-1.5 overflow-auto pr-1">
        {/* Source credit node */}
        <SourceCreditCard trail={trail} labels={labels} />

        {/* Allocation steps */}
        {traced.map((a, i) => (
          <AllocationCard
            key={a?.debit_txn_id ?? i}
            alloc={a}
            step={i + 1}
            active={i === step - 1}
            labels={labels}
          />
        ))}

        {step === 0 && (
          <div className="ml-3 py-4 text-center text-xs text-faint">
            Press play or step forward to replay how the credited funds moved chronologically.
          </div>
        )}

        {step === total && total > 0 && (
          <div className="ml-3 rounded-lg border border-line bg-line-soft/20 px-3 py-2 text-center text-xs text-muted-foreground">
            {trail.trace_status === 'exhausted'
              ? `All ${money(trail.credited_amount)} accounted for across ${total} transactions.`
              : `Traced ${money(tracedAmount)} of ${money(trail.credited_amount)} across ${total} transactions.`}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Level 2: credit selector row ───────────────────────────────────────────────

/** A single incoming credit in the Level-2 list. Compact summary from the index (no
 *  trace yet) so a list of thousands stays scannable; the trail is fetched on select. */
function CreditRow({
  credit,
  rank,
  active,
  onSelect,
}: {
  credit: MoneyTrailCredit
  rank: number
  active: boolean
  onSelect: () => void
}) {
  const sender = clean(credit.sender)
  const date = clean(credit.date)
  const narration = clean(credit.narration)

  return (
    <button
      onClick={onSelect}
      className={`flex w-full items-center gap-2 rounded-lg border px-2.5 py-1.5 text-left text-sm transition-colors ${
        active ? 'border-teal bg-teal/10' : 'border-line hover:border-teal/50 hover:bg-line-soft/40'
      }`}
    >
      <span className="grid size-5 shrink-0 place-items-center rounded-full bg-line text-[0.6rem] font-bold text-muted-foreground">
        {rank}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <span className="font-semibold text-[#cf2727]">{money(credit.credited_amount)}</span>
          {sender && <span className="truncate text-xs text-ink">from {sender}</span>}
          {date && <span className="text-[0.68rem] text-faint">{date}</span>}
          <TxnTypeBadge type={credit.txn_type} />
        </div>
        {narration && (
          <div className="truncate text-[0.66rem] text-faint" title={narration}>{narration}</div>
        )}
      </div>
      <ChevronRight className={`size-4 shrink-0 ${active ? 'text-teal' : 'text-faint'}`} />
    </button>
  )
}

// ── Level 3: fetch + render the selected credit's trail (lazy) ──────────────────

/** Fetches ONE credit's FIFO trail on demand and replays it. Keeping the fetch here
 *  (not in the index) is what lets the credit list stay instant for 10k+ credits. */
function TrailPanel({ caseId, txnId, labels }: { caseId: string; txnId: string; labels: Record<string, string> }) {
  const [trail, setTrail] = useState<MoneyTrail | null>(null)
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [message, setMessage] = useState('')
  const [downloading, setDownloading] = useState(false)
  const cache = useRef<Map<string, MoneyTrail>>(new Map())

  useEffect(() => {
    const cached = cache.current.get(txnId)
    if (cached) { setTrail(cached); setState('ready'); return }
    let cancelled = false
    setState('loading')
    api.getMoneyTrail(caseId, txnId)
      .then((t) => {
        if (cancelled) return
        cache.current.set(txnId, t)
        setTrail(t)
        setState('ready')
      })
      .catch((err) => {
        if (cancelled) return
        setState('error')
        setMessage(err instanceof ApiError ? err.message : 'Could not trace this credit.')
      })
    return () => { cancelled = true }
  }, [caseId, txnId])

  // Download this trail's transactions as a Word doc in the ORIGINAL statement layout.
  async function downloadDocx() {
    setDownloading(true)
    try {
      const res = await fetch(api.moneyTrailDocxUrl(caseId, txnId))
      if (!res.ok) throw new Error(`Export failed (${res.status})`)
      const blob = await res.blob()
      const cd = res.headers.get('content-disposition') || ''
      const m = cd.match(/filename="?([^"]+)"?/)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = m ? m[1] : `money_trail_${txnId}.docx`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch {
      /* best-effort; a failed download should never break the view */
    } finally {
      setDownloading(false)
    }
  }

  if (state === 'loading')
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
        <Loader2 className="size-5 animate-spin text-teal" />
        <p className="text-xs text-muted-foreground">Tracing this credit…</p>
      </div>
    )
  if (state === 'error') return <div className="py-16 text-center text-sm text-[#cf2727]">{message}</div>
  if (!trail) return null
  return (
    <div className="space-y-2">
      <div className="flex justify-end">
        <button
          onClick={downloadDocx}
          disabled={downloading}
          className="inline-flex items-center gap-1.5 rounded-md border border-line px-2.5 py-1 text-xs font-semibold text-muted-foreground transition-colors hover:border-teal hover:text-ink disabled:opacity-50"
          title="Download this trail's transactions as a Word document in the original statement layout"
        >
          {downloading ? <Loader2 className="size-3.5 animate-spin" /> : <FileText className="size-3.5" />}
          Download Word
        </button>
      </div>
      <TrailReplay trail={trail} labels={labels} />
    </div>
  )
}

// ── main export: Level 1 (account) → Level 2 (credit) → Level 3 (trail) ─────────

export function MoneyTrailGraph({ graph, caseId }: { graph: MoneyTrailGraphData; caseId: string }) {
  const labels = graph.labels ?? {}
  const accounts = useMemo<MoneyTrailAccount[]>(() => graph.accounts ?? [], [graph])

  // Level 1 — selected account (default: first / highest total credited).
  const [accountId, setAccountId] = useState<string>(accounts[0]?.account_id ?? '')
  const account = useMemo(
    () => accounts.find((a) => a.account_id === accountId) ?? accounts[0],
    [accounts, accountId],
  )

  const credits = useMemo(() => account?.credits ?? [], [account])

  // Level 2 — search + selected credit (by txn_id). Default to the top credit of the
  // account, and reset both when the account changes.
  const [query, setQuery] = useState('')
  const [selectedTxn, setSelectedTxn] = useState<string>(credits[0]?.txn_id ?? '')
  useEffect(() => {
    setQuery('')
    setSelectedTxn(account?.credits?.[0]?.txn_id ?? '')
  }, [account])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    // Keep the original (highest→lowest) order; carry each credit's true rank so the
    // numbering stays meaningful even while filtering.
    const withRank = credits.map((c, i) => ({ c, rank: i + 1 }))
    if (!q) return withRank
    return withRank.filter(({ c }) =>
      `${money(c.credited_amount)} ${c.sender ?? ''} ${c.narration ?? ''} ${c.date ?? ''} ${c.txn_type ?? ''} ${c.credited_amount ?? ''}`
        .toLowerCase()
        .includes(q),
    )
  }, [credits, query])

  if (accounts.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-line-soft/40 px-4 py-10 text-center text-sm text-muted-foreground">
        No incoming credits were found to trace for this case.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* ── Level 1: account selector (compact; only shown when >1 account) ── */}
      {accounts.length > 1 && (
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor="mt-account" className="text-xs font-semibold text-muted-foreground">
            Account
          </label>
          <select
            id="mt-account"
            value={account?.account_id ?? ''}
            onChange={(e) => setAccountId(e.target.value)}
            className="max-w-full flex-1 rounded-md border border-line bg-surface px-2 py-1.5 text-sm text-ink focus:border-teal focus:outline-none"
          >
            {accounts.map((a) => (
              <option key={a.account_id} value={a.account_id}>
                {a.label || a.account_id} — {a.credit_count} credit{a.credit_count === 1 ? '' : 's'} · {money(a.total_credited)}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-[minmax(0,320px)_1fr]">
        {/* ── Level 2: credit list for the selected account (sorted highest→lowest) ── */}
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-xs font-semibold text-ink">
              Incoming credits
              <span className="ml-1 font-normal text-faint">({credits.length})</span>
            </h3>
          </div>
          <div className="relative">
            <Search className="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-faint" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter by amount, sender, narration…"
              className="w-full rounded-md border border-line bg-surface py-1.5 pl-7 pr-2 text-xs text-ink focus:border-teal focus:outline-none"
            />
          </div>
          <div className="max-h-[460px] space-y-1 overflow-auto pr-1">
            {filtered.map(({ c, rank }) => (
              <CreditRow
                key={c.txn_id}
                credit={c}
                rank={rank}
                active={c.txn_id === selectedTxn}
                onSelect={() => setSelectedTxn(c.txn_id)}
              />
            ))}
            {filtered.length === 0 && (
              <div className="py-6 text-center text-xs text-faint">No credits match “{query}”.</div>
            )}
          </div>
        </div>

        {/* ── Level 3: the selected credit's money trail (fetched + replayed lazily) ── */}
        <div className="min-w-0 rounded-lg border border-line bg-line-soft/20 p-3">
          {selectedTxn ? (
            <TrailPanel key={selectedTxn} caseId={caseId} txnId={selectedTxn} labels={labels} />
          ) : (
            <div className="py-10 text-center text-sm text-faint">Select a credit to replay its money trail.</div>
          )}
        </div>
      </div>
    </div>
  )
}
