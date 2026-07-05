import { useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from 'recharts'

import type { BalanceGraphData } from '@/lib/api'

/* Balance graph: balance-over-time for the whole investigation. Toggle accounts on/off
 * to compare their balance evolution. Dense series are down-sampled for smoothness. */

const COLORS = ['#cf2727', '#2ba7a0', '#d89a20', '#7c6cf0', '#3f8cff', '#e0559b', '#6aa84f', '#b06a2c']
const MAX_POINTS = 400

function money(n: number): string {
  if (!Number.isFinite(n)) return '—'
  if (Math.abs(n) >= 1e7) return '₹' + (n / 1e7).toFixed(2) + 'Cr'
  if (Math.abs(n) >= 1e5) return '₹' + (n / 1e5).toFixed(2) + 'L'
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

function downsample<T>(arr: T[], max: number): T[] {
  if (arr.length <= max) return arr
  const step = Math.ceil(arr.length / max)
  return arr.filter((_, i) => i % step === 0 || i === arr.length - 1)
}

export function BalanceGraph({ graph }: { graph: BalanceGraphData }) {
  const labels = graph.labels ?? {}
  const accounts = graph.accounts ?? []
  const [enabled, setEnabled] = useState<Set<string>>(() => new Set(accounts.slice(0, 3).map((a) => a.account_id)))

  const { data, series } = useMemo(() => {
    // Union of all dates → one row per date, one column per enabled account (last balance seen).
    const active = accounts.filter((a) => enabled.has(a.account_id))
    const dateSet = new Set<string>()
    for (const a of active) for (const p of a.points) if (p.date) dateSet.add(p.date)
    const dates = downsample([...dateSet].sort(), MAX_POINTS)
    const perAccount = new Map<string, Map<string, number>>()
    for (const a of active) {
      const m = new Map<string, number>()
      let last = 0
      for (const p of a.points) {
        if (p.balance != null) last = p.balance
        if (p.date) m.set(p.date, last)
      }
      perAccount.set(a.account_id, m)
    }
    const data = dates.map((d) => {
      const row: Record<string, string | number> = { date: d }
      for (const a of active) {
        const m = perAccount.get(a.account_id)!
        // carry-forward last known balance up to this date
        let v: number | undefined = m.get(d)
        if (v === undefined) {
          for (let i = a.points.length - 1; i >= 0; i--) {
            const p = a.points[i]
            if (p.date && p.date <= d && p.balance != null) { v = p.balance; break }
          }
        }
        if (v !== undefined) row[a.account_id] = v
      }
      return row
    })
    const series = active.map((a, i) => ({ id: a.account_id, name: labels[a.account_id] || a.account_id, color: COLORS[i % COLORS.length] }))
    return { data, series }
  }, [accounts, enabled, labels])

  if (accounts.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-line-soft/40 px-4 py-10 text-center text-sm text-muted-foreground">
        No balance data available for this case.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1.5">
        {accounts.map((a, i) => {
          const on = enabled.has(a.account_id)
          const color = COLORS[i % COLORS.length]
          return (
            <button
              key={a.account_id}
              onClick={() =>
                setEnabled((prev) => {
                  const next = new Set(prev)
                  if (next.has(a.account_id)) next.delete(a.account_id)
                  else next.add(a.account_id)
                  return next
                })
              }
              className={`flex items-center gap-1.5 rounded-md border px-2 py-1 text-[0.7rem] ${on ? 'border-ink/30 text-ink' : 'border-line text-faint'}`}
            >
              <span className="inline-block size-2.5 rounded-full" style={{ background: on ? color : 'transparent', border: `1px solid ${color}` }} />
              {labels[a.account_id] || a.account_id}
            </button>
          )
        })}
      </div>

      <div className="h-[420px] w-full rounded-xl border border-line bg-paper p-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 16, left: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(235,235,235,0.08)" />
            <XAxis dataKey="date" tick={{ fill: '#9aa0a6', fontSize: 10 }} minTickGap={40} />
            <YAxis tickFormatter={money} tick={{ fill: '#9aa0a6', fontSize: 10 }} width={64} />
            <Tooltip
              contentStyle={{ background: '#141416', border: '1px solid rgba(235,235,235,0.16)', borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: '#ebebeb' }}
              formatter={(v, name) => [money(Number(v ?? 0)), String(name)]}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {series.map((s) => (
              <Line key={s.id} type="monotone" dataKey={s.id} name={s.name} stroke={s.color} dot={false} strokeWidth={1.6} connectNulls isAnimationActive={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
