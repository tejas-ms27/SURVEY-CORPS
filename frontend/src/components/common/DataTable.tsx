export type Column<T> = {
  key: keyof T
  label: string
  align?: 'left' | 'right'
  mono?: boolean
  render?: (row: T) => React.ReactNode
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  rows,
  empty,
}: {
  columns: Column<T>[]
  rows: T[]
  empty: string
}) {
  if (rows.length === 0) {
    return <p className="rounded-lg border border-line bg-line-soft/40 px-4 py-6 text-center text-sm text-muted-foreground">{empty}</p>
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="w-full min-w-[560px] border-collapse text-left text-sm">
        <thead className="bg-line-soft text-[0.65rem] uppercase tracking-wide text-muted-foreground">
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={`whitespace-nowrap px-3 py-2 font-bold ${col.align === 'right' ? 'text-right' : 'text-left'}`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-line-soft transition-colors hover:bg-line-soft/40">
              {columns.map((col) => (
                <td
                  key={String(col.key)}
                  className={`whitespace-nowrap px-3 py-2 text-ink ${col.mono ? 'font-mono text-xs' : ''} ${col.align === 'right' ? 'text-right tabular-nums' : ''}`}
                >
                  {col.render ? col.render(row) : String(row[col.key] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
