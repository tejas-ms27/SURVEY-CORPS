import { useState, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ChevronRight } from 'lucide-react'

type AccordionProps = {
  title: ReactNode
  right?: ReactNode
  defaultOpen?: boolean
  accent?: boolean
  children: ReactNode
}

/** A single collapsible row. Interactive, animated, keyboard-accessible. */
export function Accordion({ title, right, defaultOpen = false, accent = false, children }: AccordionProps) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div
      className={`overflow-hidden rounded-lg border bg-paper ${
        accent ? 'border-l-2 border-l-teal border-line' : 'border-line'
      }`}
    >
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-3.5 py-2.5 text-left transition-colors hover:bg-white/[0.03]"
      >
        <ChevronRight
          className={`size-3.5 flex-none text-faint transition-transform ${open ? 'rotate-90' : ''}`}
        />
        <span className="min-w-0 flex-1 truncate text-sm font-semibold text-ink">{title}</span>
        {right}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="border-t border-line-soft px-3.5 py-3">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
