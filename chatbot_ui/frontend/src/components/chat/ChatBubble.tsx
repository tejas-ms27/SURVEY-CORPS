import { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronDown, TriangleAlert } from 'lucide-react'

import detectiveUrl from '@/assets/investigator-avatar-detective.png'
import logoUrl from '@/assets/logo.png'
import type { ChatMessage } from '@/lib/api'
import Plot from '@/lib/plotly'
import { GraphFrame } from '@/components/common/GraphFrame'

function formatTime(ts?: number) {
  if (!ts) return null
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

/** Honour the figure's own height (Plotly treats layout.height as fixed) so the
 * frame is sized to fit it; fall back to a generous default. */
function chartHeight(chart: NonNullable<ChatMessage['chart']>) {
  const h = (chart.layout as { height?: number } | undefined)?.height
  return typeof h === 'number' ? h : 420
}

export function ChatBubble({ message }: { message: ChatMessage }) {
  const [citationsOpen, setCitationsOpen] = useState(false)
  const isUser = message.role === 'user'
  const citations = message.citations || []
  const time = formatTime(message.ts)

  const avatar = isUser ? (
    <img
      src={detectiveUrl}
      alt="Investigator"
      className="size-8 flex-none self-end rounded-full object-cover ring-1 ring-white/20"
    />
  ) : (
    <img
      src={logoUrl}
      alt="Assistant"
      className="size-8 flex-none self-end rounded-full object-cover ring-1 ring-white/15"
    />
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className={`flex items-end gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser && avatar}
      <div className={`flex max-w-[80%] flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
      <div
        className={`w-full rounded-xl border px-4 py-2.5 text-sm leading-relaxed ${
          isUser ? 'border-white/15 bg-white/10 text-ink' : 'border-line bg-white/[0.04] text-ink'
        }`}
      >
        {!isUser &&
          (message.structuring_alerts || []).map((alert, i) => (
            <div key={i} className="mb-2 flex items-start gap-1.5 rounded-md border border-amber/30 bg-amber/10 px-2.5 py-1.5 text-xs text-amber">
              <TriangleAlert className="mt-0.5 size-3 flex-none" />
              <span>{alert.replace(/^⚠️\s*/, '').replace(/\*\*/g, '')}</span>
            </div>
          ))}

        {!isUser && message.graph_html && (
          <div className="mb-2">
            <GraphFrame minHeight={480}>
              <iframe title="money-flow-graph" srcDoc={message.graph_html} className="h-[480px] w-full border-0" />
            </GraphFrame>
            {message.disclaimer && (
              <p className="mt-1 rounded-md border border-line bg-line-soft px-2 py-1 text-[0.68rem] text-muted-foreground">
                {message.disclaimer}
              </p>
            )}
          </div>
        )}

        {!isUser && message.chart && (
          <div className="mb-2">
            <GraphFrame minHeight={chartHeight(message.chart)}>
              <Plot
                data={(message.chart.data as never) || []}
                layout={{
                  // Keep the figure's own margins/legend/title placement so the
                  // title and legend stay in the bands the backend laid out
                  // (round 5, item 1) — only fill in sensible fallbacks.
                  autosize: true,
                  font: { family: 'DM Sans, sans-serif', size: 11 },
                  ...(message.chart.layout as object),
                }}
                useResizeHandler
                style={{ width: '100%', height: '100%' }}
                config={{ displayModeBar: false, responsive: true }}
              />
            </GraphFrame>
            {message.disclaimer && (
              <p className="mt-1 rounded-md border border-line bg-line-soft px-2 py-1 text-[0.68rem] text-muted-foreground">
                {message.disclaimer}
              </p>
            )}
          </div>
        )}

        <div className="whitespace-pre-wrap">{message.content}</div>

        {message.meta && (
          <div className={`mt-1.5 text-[0.68rem] ${isUser ? 'text-white/60' : 'text-faint'}`}>{message.meta}</div>
        )}

        {citations.length > 0 && (
          <div className="mt-2 border-t border-line/60 pt-1.5">
            <button
              onClick={() => setCitationsOpen((v) => !v)}
              className="flex items-center gap-1 text-[0.72rem] font-semibold text-muted-foreground hover:text-ink"
            >
              Citations ({citations.length})
              <ChevronDown className={`size-3 transition-transform ${citationsOpen ? 'rotate-180' : ''}`} />
            </button>
            {citationsOpen && (
              <div className="mt-1.5 space-y-1 font-mono text-[0.68rem] text-muted-foreground">
                {citations.map((c, i) => (
                  <div key={i} className="rounded bg-line-soft px-2 py-1">
                    {Object.entries(c)
                      .map(([k, v]) => `${k}: ${v}`)
                      .join(' · ')}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
        {time && <span className="px-1 text-[0.62rem] text-faint">{time}</span>}
      </div>
      {isUser && avatar}
    </motion.div>
  )
}
