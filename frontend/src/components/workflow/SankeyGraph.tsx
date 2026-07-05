import { useMemo } from 'react'

import Plot from '@/lib/plotly'
import type { SankeyGraphData } from '@/lib/api'

/* Sankey: "Money flow by transaction type" — account → transaction-type bucket
 * (UPI / NEFT / IMPS / Cash / …) → External. Same categorisation the chatbot uses,
 * rebuilt from the case transactions. Link width is proportional to the amount moved.
 * Accounts show real numbers; hover a link for the amount. */

// Distinct colour per transaction-type bucket; accounts red, External neutral.
const BUCKET_COLORS: Record<string, string> = {
  UPI: '#e8703a',
  NEFT: '#e0559b',
  RTGS: '#7c6cf0',
  IMPS: '#d89a20',
  Cheque: '#3f8cff',
  Cash: '#8b5cf6',
  Other: '#2fb3c4',
}

function money(n: number): string {
  if (!Number.isFinite(n)) return '—'
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 2 })
}

function nodeColor(node: { label: string; kind: string }): string {
  if (node.kind === 'account') return '#cf2727'
  if (node.kind === 'external') return '#57b06a'
  return BUCKET_COLORS[node.label] ?? '#9aa0a6'
}

export function SankeyGraph({ graph }: { graph: SankeyGraphData }) {
  const nodes = graph.nodes ?? []
  const links = graph.links ?? []

  const figure = useMemo(() => {
    const labels = nodes.map((n) => (n.label.length > 30 ? n.label.slice(0, 29) + '…' : n.label))
    const fullLabels = nodes.map((n) => n.label)
    const colors = nodes.map(nodeColor)
    const source = links.map((l) => l.source)
    const target = links.map((l) => l.target)
    const value = links.map((l) => l.value)
    const linkHover = links.map((l) => `${fullLabels[l.source]} → ${fullLabels[l.target]}<br>${money(l.value)}`)
    return { labels, fullLabels, colors, source, target, value, linkHover }
  }, [nodes, links])

  if (links.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-line-soft/40 px-4 py-10 text-center text-sm text-muted-foreground">
        No transaction flows to display for this case.
      </div>
    )
  }

  return (
    <div className="h-[640px] w-full overflow-hidden rounded-xl border border-line bg-white">
      <Plot
        data={[
          {
            type: 'sankey',
            orientation: 'h',
            arrangement: 'snap',
            node: {
              pad: 15,
              thickness: 18,
              line: { color: '#050505', width: 0.5 },
              label: figure.labels,
              color: figure.colors,
              customdata: figure.fullLabels,
              hovertemplate: '%{customdata}<br>₹%{value:,.2f}<extra></extra>',
            },
            link: {
              source: figure.source,
              target: figure.target,
              value: figure.value,
              color: 'rgba(120,120,120,0.28)',
              customdata: figure.linkHover,
              hovertemplate: '%{customdata}<extra></extra>',
            },
          } as unknown as Plotly.Data,
        ]}
        layout={{
          title: { text: 'Money flow by transaction type', font: { size: 15, color: '#1f2a44' } },
          font: { color: '#1f2a44', size: 12 },
          paper_bgcolor: '#ffffff',
          plot_bgcolor: '#ffffff',
          margin: { l: 10, r: 10, t: 44, b: 10 },
          autosize: true,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
      />
    </div>
  )
}
