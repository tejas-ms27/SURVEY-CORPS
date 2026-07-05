import { useMemo, useRef, useState } from 'react'
import ForceGraph2D, { type NodeObject, type LinkObject } from 'react-force-graph-2d'

import { GraphFrame } from '@/components/common/GraphFrame'
import type { MoneyFlowGraphData } from '@/lib/api'

/* Real, interactive money-flow graph rendered from the analysis run's
 * money_flow_network_3d.json (every edge traces back to a SQL txn_id). Accounts
 * observed in the statements are the red accent; reconstructed counterparties
 * are neutral. Node size scales with suspicion score, edge width with amount.
 * Click a node to isolate it and its neighbours; hover for the underlying facts. */

const OBSERVED_COLOR = '#cf2727'
const COUNTERPARTY_COLOR = '#9aa0a6'
const DIM = 'rgba(154,160,166,0.14)'
const LABEL_HIDE_THRESHOLD = 26

type RNode = {
  id: string
  label: string
  observed: boolean
  score: number
  patternCount: number
  val: number
}
type REdge = {
  source: string
  target: string
  amount: number
  date: string
  txns: string[]
  confidence: number
  patternSupported: boolean
}

function money(n: number): string {
  if (!Number.isFinite(n)) return '—'
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 2 })
}

export function MoneyFlowGraph({ graph }: { graph: MoneyFlowGraphData }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [hoverNode, setHoverNode] = useState<RNode | null>(null)
  const [hoverEdge, setHoverEdge] = useState<REdge | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  const { nodes, links, maxAmount, adjacency, labelOf } = useMemo(() => {
    const rawNodes = graph.data?.nodes ?? []
    const rawEdges = graph.data?.edges ?? []
    const labelOf = new Map<string, string>()
    const nodes: RNode[] = rawNodes.map((n) => {
      const score = Number(n.total_score) || 0
      const id = String(n.id)
      const label = (n.label && String(n.label)) || id
      labelOf.set(id, label)
      return {
        id,
        label,
        observed: Boolean(n.observed_account),
        score,
        patternCount: Number(n.pattern_count) || 0,
        val: 2 + Math.min(9, Math.sqrt(score) / 6) + (n.observed_account ? 2 : 0),
      }
    })
    const links: REdge[] = rawEdges.map((e) => ({
      source: String(e.source),
      target: String(e.target),
      amount: Number(e.amount) || 0,
      date: e.date || '',
      txns: e.txn_ids || [],
      confidence: Number(e.confidence_score) || 0,
      patternSupported: Boolean(e.pattern_supported),
    }))
    const maxAmount = links.reduce((m, l) => Math.max(m, l.amount), 0) || 1
    const adjacency = new Map<string, Set<string>>()
    for (const l of links) {
      if (!adjacency.has(l.source)) adjacency.set(l.source, new Set())
      if (!adjacency.has(l.target)) adjacency.set(l.target, new Set())
      adjacency.get(l.source)!.add(l.target)
      adjacency.get(l.target)!.add(l.source)
    }
    return { nodes, links, maxAmount, adjacency, labelOf }
  }, [graph])

  const data = useMemo(() => ({ nodes: nodes.map((n) => ({ ...n })), links: links.map((l) => ({ ...l })) }), [nodes, links])
  const dense = nodes.length > LABEL_HIDE_THRESHOLD

  const neighbourhood = useMemo(() => {
    if (!selected) return null
    const set = new Set<string>([selected])
    for (const id of adjacency.get(selected) ?? []) set.add(id)
    return set
  }, [selected, adjacency])

  const isLit = (id: string) => !neighbourhood || neighbourhood.has(id)

  if (nodes.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-line-soft/40 px-4 py-10 text-center text-sm text-muted-foreground">
        This case has no reconstructed money-flow edges to display.
      </div>
    )
  }

  const rawNodes = graph.data?.raw_filtered_node_count ?? 0
  const rawEdges = graph.data?.raw_filtered_edge_count ?? 0
  const isCapped = rawNodes > nodes.length || rawEdges > links.length

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
        <div className="flex flex-wrap gap-4">
          <span className="flex items-center gap-1.5">
            <span className="inline-block size-2.5 rounded-full" style={{ background: OBSERVED_COLOR }} /> Observed account
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block size-2 rounded-full" style={{ background: COUNTERPARTY_COLOR }} /> Counterparty
          </span>
          <span className="text-faint">{nodes.length} accounts · {links.length} flows</span>
          {isCapped && (
            <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[0.65rem] text-amber-600" title="Graph shows top reconstruction clusters only. External sender credits (e.g. from parties not in the uploaded files) are not shown as edges.">
              {rawEdges} reconstruction edges total · showing top {links.length}
            </span>
          )}
        </div>
        {selected && (
          <button
            type="button"
            onClick={() => setSelected(null)}
            className="rounded-md border border-line px-2 py-0.5 text-[0.7rem] text-ink hover:border-teal/50"
          >
            Reset selection ({labelOf.get(selected) || selected})
          </button>
        )}
      </div>

      <GraphFrame minHeight={520}>
        <div ref={containerRef} className="relative h-[520px] w-full">
          {(hoverEdge || hoverNode) && (
            <div className="pointer-events-none absolute left-3 top-3 z-10 max-w-[18rem] rounded-lg border border-line bg-paper/95 p-2.5 text-xs shadow-lg backdrop-blur">
              {hoverEdge ? (
                <>
                  <div className="font-semibold text-ink">
                    {labelOf.get(hoverEdge.source) || hoverEdge.source} → {labelOf.get(hoverEdge.target) || hoverEdge.target}
                  </div>
                  <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5 text-muted-foreground">
                    <span>Amount</span><span className="text-right text-ink">{money(hoverEdge.amount)}</span>
                    <span>Transactions</span><span className="text-right text-ink">{hoverEdge.txns.length}</span>
                    <span>Date</span><span className="text-right text-ink">{hoverEdge.date || '—'}</span>
                    <span>Confidence</span><span className="text-right text-ink">{(hoverEdge.confidence * 100).toFixed(0)}%</span>
                  </div>
                  {hoverEdge.txns.length > 0 && <div className="mt-1 text-faint">{hoverEdge.txns.length} transaction{hoverEdge.txns.length > 1 ? 's' : ''}</div>}
                </>
              ) : hoverNode ? (
                <>
                  <div className="font-semibold text-ink">{hoverNode.label}</div>
                  <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5 text-muted-foreground">
                    <span>Type</span><span className="text-right text-ink">{hoverNode.observed ? 'Observed' : 'Counterparty'}</span>
                    <span>Suspicion score</span><span className="text-right text-ink">{hoverNode.score.toFixed(0)}</span>
                    <span>Patterns</span><span className="text-right text-ink">{hoverNode.patternCount}</span>
                  </div>
                  <div className="mt-1 text-faint">Click to isolate its neighbours</div>
                </>
              ) : null}
            </div>
          )}
          <ForceGraph2D
            graphData={data}
            nodeId="id"
            linkSource="source"
            linkTarget="target"
            backgroundColor="#0a0a0b"
            linkColor={(link: LinkObject) => {
              const l = link as unknown as Omit<REdge, 'source' | 'target'> & { source: RNode | string; target: RNode | string }
              const s = typeof l.source === 'object' ? l.source.id : l.source
              const t = typeof l.target === 'object' ? l.target.id : l.target
              if (neighbourhood && !(neighbourhood.has(s) && neighbourhood.has(t))) return DIM
              return l.patternSupported ? 'rgba(207,39,39,0.55)' : 'rgba(151,163,159,0.45)'
            }}
            linkWidth={(link: LinkObject) => {
              const l = link as unknown as REdge
              return 0.6 + 3.4 * (l.amount / maxAmount)
            }}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            linkDirectionalParticles={(link: LinkObject) => {
              const l = link as unknown as Omit<REdge, 'source' | 'target'> & { source: RNode | string; target: RNode | string }
              const s = typeof l.source === 'object' ? l.source.id : l.source
              const t = typeof l.target === 'object' ? l.target.id : l.target
              if (neighbourhood && !(neighbourhood.has(s) && neighbourhood.has(t))) return 0
              return l.patternSupported ? 2 : 0
            }}
            linkDirectionalParticleWidth={2}
            onLinkHover={(link) => {
              if (!link) return setHoverEdge(null)
              const l = link as unknown as Omit<REdge, 'source' | 'target'> & { source: RNode | string; target: RNode | string }
              setHoverEdge({
                ...l,
                source: typeof l.source === 'object' ? l.source.id : l.source,
                target: typeof l.target === 'object' ? l.target.id : l.target,
              })
            }}
            nodeRelSize={4}
            nodeVal={(node: NodeObject) => (node as unknown as RNode).val}
            nodeColor={(node: NodeObject) => {
              const n = node as unknown as RNode
              if (!isLit(n.id)) return DIM
              return n.observed ? OBSERVED_COLOR : COUNTERPARTY_COLOR
            }}
            nodeLabel={() => ''}
            onNodeHover={(node) => setHoverNode(node ? (node as unknown as RNode) : null)}
            onNodeClick={(node) => {
              const n = node as unknown as RNode
              setSelected((cur) => (cur === n.id ? null : n.id))
            }}
            cooldownTicks={90}
            cooldownTime={5000}
            nodeCanvasObjectMode={() => 'after'}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const n = node as unknown as RNode & { x: number; y: number }
              if (!isLit(n.id)) return
              const showLabel = !dense || n.observed || n.id === hoverNode?.id || n.id === selected
              if (!showLabel) return
              const fontSize = (n.observed ? 10 : 8.5) / globalScale
              ctx.font = `${n.observed ? 600 : 400} ${fontSize}px "DM Sans", sans-serif`
              ctx.fillStyle = '#ebebeb'
              ctx.textAlign = 'center'
              ctx.textBaseline = 'top'
              const offset = (n.val + 3) / globalScale
              ctx.fillText(String(n.label || n.id).slice(0, 28), n.x, n.y + offset)
            }}
            width={containerRef.current?.clientWidth}
            height={520}
          />
        </div>
      </GraphFrame>
    </div>
  )
}
