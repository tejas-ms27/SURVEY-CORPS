import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export function SimpleBarChart({
  data,
  xKey,
  yKey,
  color,
}: {
  data: Record<string, unknown>[]
  xKey: string
  yKey: string
  color: string
}) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line-soft)" />
        <XAxis
          dataKey={xKey}
          tick={{ fontSize: 11, fill: 'var(--muted-ink)' }}
          axisLine={{ stroke: 'var(--line)' }}
          tickLine={false}
          interval={0}
          angle={-18}
          textAnchor="end"
          height={48}
        />
        <YAxis tick={{ fontSize: 11, fill: 'var(--muted-ink)' }} axisLine={false} tickLine={false} width={32} />
        <Tooltip
          cursor={{ fill: 'var(--line-soft)' }}
          contentStyle={{
            borderRadius: 8,
            border: '1px solid var(--line)',
            background: 'var(--paper)',
            color: 'var(--ink)',
            fontSize: 12,
            boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
          }}
          labelStyle={{ color: 'var(--ink)' }}
          itemStyle={{ color: 'var(--ink)' }}
        />
        <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} maxBarSize={40} />
      </BarChart>
    </ResponsiveContainer>
  )
}
