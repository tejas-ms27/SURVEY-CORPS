import { useState } from 'react'
import { Check, Copy, RefreshCw, Trash2 } from 'lucide-react'

import logoUrl from '@/assets/logo.png'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { api } from '@/lib/api'
import { useCases } from '@/hooks/useCases'
import { useAppStore } from '@/store/useAppStore'

export function TopNav() {
  const { cases, activeCaseId, setActiveCase, refresh } = useCases()
  const setFlash = useAppStore((s) => s.setFlash)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [copied, setCopied] = useState(false)

  async function copyCaseId() {
    if (!activeCaseId) return
    try {
      await navigator.clipboard.writeText(activeCaseId)
      setCopied(true)
      setTimeout(() => setCopied(false), 1400)
    } catch {
      /* clipboard unavailable — the tooltip still shows the full id */
    }
  }

  async function handleDelete() {
    if (!activeCaseId) return
    setDeleting(true)
    try {
      const res = await api.deleteCase(activeCaseId)
      setFlash(res.message)
      setActiveCase(res.next_active)
      await refresh()
    } finally {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  return (
    <header className="flex h-16 flex-none items-center gap-6 border-b border-white/10 bg-navy px-6 text-white">
      <div className="flex items-center gap-2.5">
        <img src={logoUrl} alt="Survey Corps" className="size-9 flex-none rounded-full object-cover" />
        <div className="leading-tight">
          <div className="font-display text-sm font-extrabold tracking-wide text-white">SURVEY CORPS</div>
          <div className="text-[0.58rem] uppercase tracking-widest text-white/45">Financial Forensics Engine</div>
        </div>
      </div>

      {/* Single guided flow — no separate Extraction / Analysis / Reports tabs. */}
      <div className="hidden items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 sm:flex">
        <span className="inline-block size-1.5 rounded-full bg-teal" />
        <span className="text-[0.62rem] font-bold uppercase tracking-[0.2em] text-white/55">Open case file</span>
      </div>

      <div className="ml-auto flex items-center gap-2.5">
        {/* Single case badge (round 5, item 4): the name is truncated with an
            ellipsis and the full id lives in the tooltip; click copies it. */}
        <button
          type="button"
          onClick={copyCaseId}
          disabled={!activeCaseId}
          title={activeCaseId ? `${activeCaseId} — click to copy` : undefined}
          className="group hidden max-w-[240px] items-center gap-2 rounded-lg border border-lime/20 bg-white/5 px-3 py-1.5 leading-none transition-colors hover:border-lime/40 hover:bg-white/10 disabled:cursor-default disabled:hover:border-lime/20 disabled:hover:bg-white/5 sm:flex"
        >
          <span className="text-[0.58rem] uppercase tracking-widest text-white/40">Case</span>
          <span className="min-w-0 flex-1 truncate text-left font-display text-xs font-bold tracking-wide text-lime">
            {activeCaseId || 'No case loaded'}
          </span>
          {activeCaseId &&
            (copied ? (
              <Check className="size-3 flex-none text-green" />
            ) : (
              <Copy className="size-3 flex-none text-white/30 transition-colors group-hover:text-white/60" />
            ))}
        </button>

        {cases.length > 1 && (
          <Select value={activeCaseId || undefined} onValueChange={(v) => setActiveCase(v)}>
            <SelectTrigger className="h-9 w-[150px] border-lime/20 bg-white/5 text-white [&_svg]:text-white/60">
              <SelectValue placeholder="Switch case" />
            </SelectTrigger>
            <SelectContent>
              {cases.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        <Button
          variant="ghost"
          size="sm"
          className="text-white/70 hover:bg-white/10 hover:text-white"
          onClick={() => refresh()}
        >
          <RefreshCw className="size-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          disabled={!activeCaseId}
          className="text-white/70 hover:bg-red/20 hover:text-red"
          onClick={() => setConfirmDelete(true)}
        >
          <Trash2 className="size-3.5" />
        </Button>
      </div>

      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete case permanently?</DialogTitle>
            <DialogDescription>
              This removes <b>{activeCaseId}</b>'s files, index and chat history. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDelete(false)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={deleting} onClick={handleDelete}>
              {deleting ? 'Deleting…' : 'Yes, delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </header>
  )
}
