import { useEffect, useState } from 'react'
import { Download } from 'lucide-react'

import { MetricCard } from '@/components/common/MetricCard'
import { DataTable } from '@/components/common/DataTable'
import { Accordion } from '@/components/common/Accordion'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  api,
  type AccountRow,
  type DuplicateRow,
  type ExtractionResult,
  type FlagRow,
} from '@/lib/api'

const DOWNLOAD_LABELS: Record<string, string> = {
  clean: 'Clean transactions (CSV)',
  flagged: 'Flagged rows (CSV)',
  duplicates: 'Duplicates (CSV)',
  metadata: 'Extraction metadata (JSON)',
}

function fileName(rec: Record<string, unknown>): string {
  return String(rec.file || rec.account_ref || 'file')
}

export function ExtractionResults({ result, caseId }: { result: ExtractionResult; caseId: string }) {
  const [accounts, setAccounts] = useState<AccountRow[]>([])
  const [flags, setFlags] = useState<FlagRow[]>([])
  const [duplicates, setDuplicates] = useState<DuplicateRow[]>([])

  useEffect(() => {
    if (!caseId) return
    api.getAccounts(caseId).then((r) => setAccounts(r.accounts)).catch(() => {})
    api.getFlags(caseId).then((r) => setFlags(r.flags)).catch(() => {})
    api.getDuplicates(caseId).then((r) => setDuplicates(r.duplicates)).catch(() => {})
  }, [caseId])

  const perFile = result.per_file || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-bold text-ink">Extraction complete</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          {result.files_processed} file(s) parsed into one verified transaction table in {result.elapsed_label}.
        </p>
      </div>

      {/* Dashboard cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricCard label="Accounts" value={accounts.length || '—'} />
        <MetricCard label="Clean rows" value={result.clean_rows} />
        <MetricCard label="Flagged rows" value={result.flagged_rows} />
        <MetricCard label="Indexed chunks" value={result.indexed_chunks} />
      </div>

      {result.files_failed.length > 0 && (
        <Card className="border-l-2 border-l-red border-line px-4 py-3 text-xs text-red">
          {result.files_failed.length} file(s) could not be parsed: {result.files_failed.join(', ')}
        </Card>
      )}

      {/* Per-account summary */}
      <div>
        <h3 className="mb-2 text-sm font-bold text-ink">Per-account summary</h3>
        <DataTable
          columns={[
            { key: 'holder', label: 'Holder' },
            { key: 'bank', label: 'Bank' },
            { key: 'account', label: 'Account', mono: true },
            { key: 'statement_period', label: 'Period' },
            { key: 'opening_balance', label: 'Opening', mono: true, align: 'right' },
            { key: 'closing_balance', label: 'Closing', mono: true, align: 'right' },
            { key: 'transactions', label: 'Txns', align: 'right' },
            { key: 'flagged', label: 'Flagged', align: 'right' },
          ]}
          rows={accounts}
          empty="No accounts parsed."
        />
      </div>

      {/* Conditional flag + duplicate summaries */}
      {(flags.length > 0 || duplicates.length > 0) && (
        <div className="grid gap-4 sm:grid-cols-2">
          {flags.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-bold text-ink">Flag reason breakdown</h3>
              <DataTable
                columns={[
                  { key: 'flag_reason', label: 'Reason' },
                  { key: 'count', label: 'Rows', align: 'right' },
                ]}
                rows={flags}
                empty="No flagged rows."
              />
            </div>
          )}
          {duplicates.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-bold text-ink">Duplicate summary</h3>
              <DataTable
                columns={[
                  { key: 'account_number', label: 'Account', mono: true },
                  { key: 'duplicates', label: 'Duplicates', align: 'right' },
                ]}
                rows={duplicates}
                empty="No duplicates."
              />
            </div>
          )}
        </div>
      )}

      {/* Metadata as a table (not raw JSON) */}
      <div>
        <h3 className="mb-2 text-sm font-bold text-ink">Extracted files</h3>
        <DataTable
          columns={[
            { key: 'file', label: 'File', render: (r) => fileName(r as Record<string, unknown>) },
            { key: 'route', label: 'Format' },
            { key: 'tier', label: 'Parser tier' },
            {
              key: 'reconciliation_rate',
              label: 'Reconciliation',
              align: 'right',
              render: (r) => {
                const v = (r as Record<string, unknown>).reconciliation_rate
                return typeof v === 'number' ? `${Math.round(v * 100)}%` : '—'
              },
            },
            {
              key: 'rows_clean',
              label: 'Rows',
              align: 'right',
              render: (r) => String((r as Record<string, unknown>).rows_clean ?? '—'),
            },
            {
              key: 'llm_calls',
              label: 'LLM calls',
              align: 'right',
              render: (r) => String((r as Record<string, unknown>).llm_calls ?? 0),
            },
          ]}
          rows={perFile as Record<string, unknown>[]}
          empty="No file records."
        />
      </div>

      {/* Downloads */}
      <div>
        <h3 className="mb-2 text-sm font-bold text-ink">Download extracted data</h3>
        <div className="flex flex-wrap gap-2">
          {result.downloads_available.map((key) => (
            <Button key={key} variant="outline" size="sm" asChild>
              <a href={api.downloadUrl(caseId, key)}>
                <Download className="size-3.5" /> {DOWNLOAD_LABELS[key] || key}
              </a>
            </Button>
          ))}
          {result.downloads_available.length === 0 && (
            <p className="text-xs text-muted-foreground">No downloadable files for this run.</p>
          )}
        </div>
      </div>

      {/* Advanced raw metadata, collapsed by default */}
      <Accordion title="Advanced metadata (per-file audit)">
        <div className="space-y-2">
          {perFile.map((rec, i) => (
            <details key={i} className="rounded border border-line-soft bg-canvas/50 p-2.5">
              <summary className="cursor-pointer text-xs font-medium text-ink">{fileName(rec)}</summary>
              <pre className="mt-2 overflow-x-auto text-[0.68rem] leading-relaxed text-muted-foreground">
                {JSON.stringify(rec, null, 2)}
              </pre>
            </details>
          ))}
        </div>
      </Accordion>
    </div>
  )
}
