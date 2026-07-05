import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

import { Card } from '@/components/ui/card'

function useCountUp(target: number, durationMs = 500) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    let frame: number
    const start = performance.now()
    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / durationMs)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(eased * target))
      if (progress < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [target, durationMs])
  return value
}

export function MetricCard({ label, value }: { label: string; value: number | string }) {
  // Numbers count up on mount; text values (percentages, statuses) render as-is.
  const numeric = typeof value === 'number'
  const animated = useCountUp(numeric ? value : 0)
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, scale: 1.03 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="px-4 py-3.5 transition-colors hover:border-teal/50">
        <div className="text-[0.68rem] font-bold uppercase tracking-widest text-faint">{label}</div>
        <div className="mt-1 font-display text-2xl font-extrabold text-ink tabular-nums">
          {numeric ? animated : value}
        </div>
      </Card>
    </motion.div>
  )
}
