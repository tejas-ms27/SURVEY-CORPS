import { useMemo, useRef, useState } from 'react'
import ForceGraph2D, { type NodeObject, type LinkObject } from 'react-force-graph-2d'

import { GraphFrame } from '@/components/common/GraphFrame'
import type { GraphResponse } from '@/lib/api'

// App palette (round 3): accounts in the red accent, counterparties in a
// neutral grey, on a dark graph canvas.
const ACCOUNT_COLOR = '#cf2727'
const COUNTERPARTY_COLOR = '#9aa0a6'

// Past this many nodes, always-on counterparty labels collide, so they collapse
// to hover-only (accounts always keep their label). Round 5, item 2.
const LABEL_HIDE_THRESHOLD = 18

export function RelationshipGraph({ graph }: { graph: GraphResponse }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [hoverId, setHoverId] = useState<string | number | null>(null)

  const data = useMemo(
    () => ({
      nodes: graph.nodes.map((n) => ({ ...n })),
      links: graph.edges.map((e) => ({ ...e })),
    }),
    [graph],
  )

  const dense = data.nodes.length > LABEL_HIDE_THRESHOLD

  if (graph.nodes.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-line-soft/40 px-4 py-8 text-center text-sm text-muted-foreground">
        No clean counterparty hints were found in transaction narrations for this case.
      </div>
    )
  }

  return (
    <GraphFrame minHeight={480}>
      <div ref={containerRef} className="relative h-[480px] w-full">
        <div className="pointer-events-none absolute left-3 top-3 z-10 flex flex-col gap-1 text-xs font-medium text-muted-foreground">
          <div className="flex gap-4">
            <span className="flex items-center gap-1.5">
              <span className="inline-block size-2.5 rounded-full" style={{ background: ACCOUNT_COLOR }} /> Account
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block size-2 rounded-full" style={{ background: COUNTERPARTY_COLOR }} /> Counterparty
            </span>
          </div>
          {dense && <span className="text-[0.68rem] text-faint">Hover a node to reveal its label</span>}
        </div>
        <ForceGraph2D
          graphData={data}
          nodeId="id"
          linkSource="source"
          linkTarget="target"
          backgroundColor="#0a0a0b"
          linkColor={() => 'rgba(151, 163, 159, 0.45)'}
          linkWidth={(link: LinkObject) => 1 + Math.min(3, ((link as unknown as { count: number }).count || 1) * 0.4)}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          nodeRelSize={5}
          nodeVal={(node: NodeObject) => ((node as unknown as { type: string }).type === 'account' ? 6 : 2.4)}
          nodeColor={(node: NodeObject) =>
            (node as unknown as { type: string }).type === 'account' ? ACCOUNT_COLOR : COUNTERPARTY_COLOR
          }
          nodeLabel={(node: NodeObject) => (node as unknown as { label: string }).label}
          onNodeHover={(node) => setHoverId(node ? (node as unknown as { id: string | number }).id : null)}
          // Stop the simulation once it settles so the layout freezes instead of
          // drifting; drag/zoom/pan stay interactive (round 5, item 2).
          cooldownTicks={80}
          cooldownTime={4000}
          nodeCanvasObjectMode={() => 'after'}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const n = node as unknown as { id: string | number; x: number; y: number; label: string; type: string }
            // Past the threshold, only draw the label for accounts or the node
            // currently under the cursor — everything else stays clean.
            if (dense && n.type !== 'account' && n.id !== hoverId) return
            const fontSize = (n.type === 'account' ? 11 : 9) / globalScale
            ctx.font = `${n.type === 'account' ? 600 : 400} ${fontSize}px "DM Sans", sans-serif`
            ctx.fillStyle = '#ebebeb'
            ctx.textAlign = 'center'
            ctx.textBaseline = 'top'
            const offset = (n.type === 'account' ? 9 : 5) / globalScale
            ctx.fillText((n.label || '').slice(0, 22), n.x, n.y + offset)
          }}
          width={containerRef.current?.clientWidth}
          height={480}
        />
      </div>
    </GraphFrame>
  )
}
