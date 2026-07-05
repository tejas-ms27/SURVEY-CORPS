import { useMemo, useRef, useState, useCallback } from 'react'
import ForceGraph2D, { type NodeObject, type LinkObject } from 'react-force-graph-2d'

import { GraphFrame } from '@/components/common/GraphFrame'
import type { FullFlowGraphData, FullFlowNode, FullFlowEdge } from '@/lib/api'

/* Full Transaction Graph — the complete money-flow knowledge graph. Every eligible
 * transaction becomes an edge from its account (large red hub) to a counterparty leaf.
 * Counterparties come from the resolver when available, otherwise the name is mined from
 * the narration (UPI/IMPS/NEFT payee, "frm NAME", etc.) so NO transaction is dropped.
 * Toggle accounts on/off to view one account's fan-out (like a single-account hairball)
 * or several at once. Amount filter trims small transactions. Everything traces to SQL. */

// ── colours by counterparty kind ──────────────────────────────────────────────
const KIND_COLOR: Record<string, string> = {
  observed: '#cf2727',   // your uploaded accounts
  person:   '#e8703a',   // a named individual/business mined from narration or resolver
  upi:      '#d89a20',   // a UPI handle
  account:  '#3f8cff',   // a bank account number
  charge:   '#7c6cf0',   // bank charges / tax / ATM / interest
  unknown:  '#9aa0a6',   // couldn't identify the other party
  other:    '#9aa0a6',
}
const KIND_LABEL: Record<string, string> = {
  observed: 'Your accounts',
  person:   'Named party',
  upi:      'UPI handle',
  account:  'Bank account',
  charge:   'Charges / tax / ATM',
  unknown:  'Unidentified',
}
// Distinct hub colour per observed account so multi-account views stay legible.
const ACCOUNT_COLORS = ['#cf2727', '#2ba7a0', '#d89a20', '#7c6cf0', '#3f8cff', '#e0559b', '#6aa84f', '#b06a2c']

const DIM = 'rgba(154,160,166,0.08)'
const DIM_EDGE = 'rgba(154,160,166,0.05)'
const LABEL_MIN_VOLUME = 20000     // only label bigger counterparties to avoid clutter
const AMOUNT_STEPS = [0, 100, 500, 1000, 5000, 10000, 50000]

function money(n: number): string {
  if (!Number.isFinite(n) || n === 0) return '₹0'
  if (n >= 1e7) return '₹' + (n / 1e7).toFixed(2) + 'Cr'
  if (n >= 1e5) return '₹' + (n / 1e5).toFixed(2) + 'L'
  if (n >= 1e3) return '₹' + (n / 1e3).toFixed(1) + 'K'
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

export function FullFlowGraph({ graph }: { graph: FullFlowGraphData }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const fgRef = useRef<{ zoom: (k: number, ms: number) => void; zoomToFit: (ms: number, px: number) => void } | null>(null)

  const accountRoster = graph.accounts ?? []
  // Colour per account id, and a default: show the busiest account only if the graph is huge.
  const accountColor = useMemo(() => {
    const m = new Map<string, string>()
    accountRoster.forEach((a, i) => m.set(a.id, ACCOUNT_COLORS[i % ACCOUNT_COLORS.length]))
    return m
  }, [accountRoster])

  const [enabledAccounts, setEnabledAccounts] = useState<Set<string>>(() => {
    // Default: all accounts on if the graph is small; otherwise start with the busiest one
    // so the first paint is legible (user can enable the rest).
    if ((graph.nodes?.length ?? 0) <= 400) return new Set(accountRoster.map((a) => a.id))
    const busiest = [...accountRoster].sort((a, b) => b.txn_count - a.txn_count)[0]
    return new Set(busiest ? [busiest.id] : accountRoster.map((a) => a.id))
  })

  const [minAmount, setMinAmount] = useState(() => ((graph.nodes?.length ?? 0) > 800 ? 500 : 0))
  const [selected, setSelected] = useState<string | null>(null)
  const [hoverNode, setHoverNode] = useState<FullFlowNode | null>(null)
  const [hoverEdge, setHoverEdge] = useState<FullFlowEdge | null>(null)

  const toggleAccount = useCallback((id: string) => {
    setSelected(null)
    setEnabledAccounts((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }, [])

  // ── filter to enabled accounts + amount, then build the render graph ────────
  const { nodes, links, maxAmount, maxVolume, adjacency, labelMap, shownEdges, shownTxns } = useMemo(() => {
    const nodeMap = new Map(graph.nodes.map((n) => [n.id, n]))
    const isObserved = (id: string) => nodeMap.get(id)?.kind === 'observed'

    // Keep an edge if it touches an enabled account and clears the amount floor.
    const keptEdges = graph.edges.filter((e) => {
      if (e.amount < minAmount) return false
      const sObs = isObserved(e.source), tObs = isObserved(e.target)
      const touchesEnabled =
        (sObs && enabledAccounts.has(e.source)) || (tObs && enabledAccounts.has(e.target))
      return touchesEnabled
    })

    const activeIds = new Set<string>()
    for (const e of keptEdges) { activeIds.add(e.source); activeIds.add(e.target) }
    for (const id of enabledAccounts) activeIds.add(id)  // keep hub even with no edges

    const nodes = [...activeIds]
      .map((id) => nodeMap.get(id))
      .filter((n): n is FullFlowNode => Boolean(n))
      .map((n) => ({ ...n }))

    const maxAmount = keptEdges.reduce((m, e) => Math.max(m, e.amount), 1)
    const maxVolume = nodes.reduce((m, n) => Math.max(m, n.total_volume), 1)
    const labelMap = new Map(nodes.map((n) => [n.id, n.label || n.id]))

    const adjacency = new Map<string, Set<string>>()
    for (const e of keptEdges) {
      if (!adjacency.has(e.source)) adjacency.set(e.source, new Set())
      if (!adjacency.has(e.target)) adjacency.set(e.target, new Set())
      adjacency.get(e.source)!.add(e.target)
      adjacency.get(e.target)!.add(e.source)
    }
    const shownTxns = keptEdges.reduce((s, e) => s + e.txn_count, 0)

    return { nodes, links: keptEdges.map((e) => ({ ...e })), maxAmount, maxVolume, adjacency, labelMap, shownEdges: keptEdges.length, shownTxns }
  }, [graph, enabledAccounts, minAmount])

  const data = useMemo(
    () => ({ nodes: nodes.map((n) => ({ ...n })), links: links.map((l) => ({ ...l })) }),
    [nodes, links],
  )

  const neighbourhood = useMemo(() => {
    if (!selected) return null
    const s = new Set([selected])
    for (const id of adjacency.get(selected) ?? []) s.add(id)
    return s
  }, [selected, adjacency])

  const isLit = useCallback((id: string) => !neighbourhood || neighbourhood.has(id), [neighbourhood])

  // ── node appearance ────────────────────────────────────────────────────────
  const nodeVal = useCallback((node: NodeObject) => {
    const n = node as unknown as FullFlowNode
    if (n.kind === 'observed') return 18 + Math.sqrt(n.total_volume / maxVolume) * 12
    return 2 + Math.sqrt(n.total_volume / maxVolume) * 7
  }, [maxVolume])

  const nodeColor = useCallback((node: NodeObject) => {
    const n = node as unknown as FullFlowNode
    if (!isLit(n.id)) return DIM
    if (n.kind === 'observed') return accountColor.get(n.id) ?? KIND_COLOR.observed
    return KIND_COLOR[n.kind] ?? KIND_COLOR.other
  }, [isLit, accountColor])

  // ── edge appearance ────────────────────────────────────────────────────────
  const linkColor = useCallback((link: LinkObject) => {
    const l = link as unknown as Omit<FullFlowEdge, 'source' | 'target'> & { source: FullFlowNode | string; target: FullFlowNode | string }
    const s = typeof l.source === 'object' ? l.source.id : l.source
    const t = typeof l.target === 'object' ? l.target.id : l.target
    if (!isLit(s) || !isLit(t)) return DIM_EDGE
    const sKind = typeof l.source === 'object' ? l.source.kind : null
    const tKind = typeof l.target === 'object' ? l.target.kind : null
    if (sKind === 'observed' && tKind === 'observed') return 'rgba(43,167,160,0.85)'  // account↔account
    return 'rgba(154,160,166,0.30)'
  }, [isLit])

  const linkWidth = useCallback((link: LinkObject) => {
    const l = link as unknown as FullFlowEdge
    return 0.4 + 3.2 * Math.sqrt(l.amount / maxAmount)
  }, [maxAmount])

  // ── canvas labels (hubs always; big counterparties + selection/hover) ───────
  const nodeCanvasObject = useCallback((node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const n = node as unknown as FullFlowNode & { x: number; y: number }
    if (!isLit(n.id)) return
    const isSel = n.id === selected
    const isHov = n.id === hoverNode?.id
    const show = n.kind === 'observed' || n.total_volume >= LABEL_MIN_VOLUME || isSel || isHov
    if (!show) return

    const label = String(n.label || n.id)
    const fontSize = (n.kind === 'observed' ? 12 : 9) / globalScale
    ctx.font = `${n.kind === 'observed' ? '700' : '400'} ${fontSize}px "DM Sans", sans-serif`
    const textW = ctx.measureText(label).width
    const pad = 2 / globalScale
    const r = (nodeVal(node) as number) * 0.9 / globalScale + 2 / globalScale

    ctx.fillStyle = 'rgba(10,10,11,0.80)'
    ctx.beginPath()
    ctx.roundRect(n.x - textW / 2 - pad, n.y + r, textW + pad * 2, fontSize + pad * 2, 2 / globalScale)
    ctx.fill()
    ctx.fillStyle = n.kind === 'observed' ? '#ffffff' : '#cfcfcf'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.fillText(label.slice(0, 34), n.x, n.y + r + pad / 2)
  }, [isLit, selected, hoverNode, nodeVal])

  if (accountRoster.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-line-soft/40 px-4 py-10 text-center text-sm text-muted-foreground">
        No transactions found. Run analysis to build the graph.
      </div>
    )
  }

  const unresolvedNote = graph.total_transactions - graph.resolved_transactions

  return (
    <div className="space-y-2.5">
      {/* Account toggles — pick which accounts' transactions to show */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-xs font-semibold text-muted-foreground">Accounts:</span>
        {accountRoster.map((a) => {
          const on = enabledAccounts.has(a.id)
          const color = accountColor.get(a.id) ?? '#cf2727'
          return (
            <button
              key={a.id}
              onClick={() => toggleAccount(a.id)}
              className={`flex items-center gap-1.5 rounded-md border px-2 py-1 text-[0.7rem] transition-colors ${
                on ? 'border-ink/30 text-ink' : 'border-line text-faint'
              }`}
              title={`${a.txn_count} transactions`}
            >
              <span className="inline-block size-2.5 rounded-full" style={{ background: on ? color : 'transparent', border: `1px solid ${color}` }} />
              {a.label}
              <span className="text-faint">· {a.txn_count}</span>
            </button>
          )
        })}
        <button
          onClick={() => { setSelected(null); setEnabledAccounts(new Set(accountRoster.map((a) => a.id))) }}
          className="rounded-md border border-line px-2 py-1 text-[0.65rem] text-muted-foreground hover:text-ink"
        >
          Show all
        </button>
      </div>

      {/* Amount filter + stats + zoom */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <span className="shrink-0">Min amount:</span>
          <div className="flex gap-1">
            {AMOUNT_STEPS.map((step) => (
              <button
                key={step}
                onClick={() => { setMinAmount(step); setSelected(null) }}
                className={`rounded px-2 py-0.5 text-[0.65rem] font-semibold transition-colors ${
                  minAmount === step ? 'border border-teal/40 bg-teal/20 text-teal' : 'border border-line text-muted-foreground hover:text-ink'
                }`}
              >
                {step === 0 ? 'All' : money(step)}
              </button>
            ))}
          </div>
        </div>
        <span className="text-xs text-faint">
          {nodes.length} nodes · {shownEdges} connections · {shownTxns.toLocaleString()} txns shown
        </span>
        {selected && (
          <button onClick={() => setSelected(null)} className="rounded-md border border-line px-2 py-0.5 text-[0.7rem] text-ink hover:border-teal/50">
            Reset ({labelMap.get(selected) || selected})
          </button>
        )}
        <div className="ml-auto flex gap-1">
          <button className="rounded border border-line px-2 py-0.5 text-[0.7rem] text-muted-foreground hover:text-ink" onClick={() => fgRef.current?.zoom(1.5, 400)}>+</button>
          <button className="rounded border border-line px-2 py-0.5 text-[0.7rem] text-muted-foreground hover:text-ink" onClick={() => fgRef.current?.zoom(0.67, 400)}>−</button>
          <button className="rounded border border-line px-2 py-0.5 text-[0.7rem] text-muted-foreground hover:text-ink" onClick={() => fgRef.current?.zoomToFit(400, 40)}>Fit</button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
        {(['observed', 'person', 'upi', 'account', 'charge', 'unknown'] as const).map((kind) => (
          <span key={kind} className="flex items-center gap-1.5">
            <span className="inline-block size-2.5 rounded-full" style={{ background: KIND_COLOR[kind] }} />
            {KIND_LABEL[kind]}
          </span>
        ))}
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-5 rounded" style={{ background: 'rgba(43,167,160,0.85)' }} />
          Between your accounts
        </span>
      </div>

      {/* Graph */}
      <GraphFrame minHeight={600}>
        <div ref={containerRef} className="relative h-[600px] w-full">
          {(hoverNode || hoverEdge) && (
            <div className="pointer-events-none absolute left-3 top-3 z-10 max-w-[22rem] rounded-lg border border-line bg-paper/95 p-3 text-xs shadow-lg backdrop-blur">
              {hoverNode ? (
                <>
                  <div className="flex items-center gap-2">
                    <span className="inline-block size-2.5 shrink-0 rounded-full" style={{ background: hoverNode.kind === 'observed' ? (accountColor.get(hoverNode.id) ?? KIND_COLOR.observed) : (KIND_COLOR[hoverNode.kind] ?? '#9aa0a6') }} />
                    <span className="font-semibold text-ink">{hoverNode.label || hoverNode.id}</span>
                  </div>
                  <div className="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-0.5 text-muted-foreground">
                    <span>Type</span><span className="text-right text-ink">{KIND_LABEL[hoverNode.kind] ?? hoverNode.kind}</span>
                    <span>Total volume</span><span className="text-right text-ink">{money(hoverNode.total_volume)}</span>
                    {hoverNode.kind === 'observed' && <><span>Transactions</span><span className="text-right text-ink">{hoverNode.txn_count}</span></>}
                  </div>
                  <div className="mt-1 text-faint">Click to isolate its connections</div>
                </>
              ) : hoverEdge ? (
                <>
                  <div className="font-semibold text-ink">
                    {labelMap.get(hoverEdge.source) || hoverEdge.source}
                    {' → '}
                    {labelMap.get(hoverEdge.target) || hoverEdge.target}
                  </div>
                  <div className="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-0.5 text-muted-foreground">
                    <span>Total amount</span><span className="text-right text-ink">{money(hoverEdge.amount)}</span>
                    <span>Transactions</span><span className="text-right text-ink">{hoverEdge.txn_count}</span>
                    <span>Type</span><span className="text-right text-ink">{hoverEdge.txn_type}</span>
                    <span>Period</span><span className="text-right text-ink">{hoverEdge.first_date}{hoverEdge.first_date !== hoverEdge.last_date ? ` – ${hoverEdge.last_date}` : ''}</span>
                  </div>
                  {hoverEdge.sample_narration && (
                    <div className="mt-1.5 truncate text-[0.65rem] text-faint" title={hoverEdge.sample_narration}>{hoverEdge.sample_narration}</div>
                  )}
                </>
              ) : null}
            </div>
          )}

          <ForceGraph2D
            ref={fgRef as unknown as React.MutableRefObject<never>}
            graphData={data}
            nodeId="id"
            linkSource="source"
            linkTarget="target"
            backgroundColor="#0a0a0b"
            nodeVal={nodeVal}
            nodeColor={nodeColor}
            nodeLabel={() => ''}
            nodeCanvasObjectMode={() => 'after'}
            nodeCanvasObject={nodeCanvasObject}
            onNodeHover={(node) => setHoverNode(node ? (node as unknown as FullFlowNode) : null)}
            onNodeClick={(node) => {
              const n = node as unknown as FullFlowNode
              setSelected((cur) => (cur === n.id ? null : n.id))
            }}
            linkColor={linkColor}
            linkWidth={linkWidth}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            onLinkHover={(link) => {
              if (!link) return setHoverEdge(null)
              const l = link as unknown as Omit<FullFlowEdge, 'source' | 'target'> & { source: FullFlowNode | string; target: FullFlowNode | string }
              setHoverEdge({
                ...l,
                source: typeof l.source === 'object' ? l.source.id : l.source,
                target: typeof l.target === 'object' ? l.target.id : l.target,
              })
            }}
            cooldownTicks={100}
            warmupTicks={20}
            cooldownTime={8000}
            width={containerRef.current?.clientWidth}
            height={600}
          />
        </div>
      </GraphFrame>

      {/* Footer */}
      <p className="text-[0.68rem] text-faint">
        Every eligible transaction is shown: {graph.total_transactions.toLocaleString()} total.
        {' '}Counterparties come from the resolver where available, otherwise the name is read from the narration.
        {unresolvedNote > 0 && ` Transactions with no identifiable party appear as individual "Unidentified" leaves.`}
        {' '}Each edge traces back to real transactions in the SQL database.
      </p>
    </div>
  )
}
