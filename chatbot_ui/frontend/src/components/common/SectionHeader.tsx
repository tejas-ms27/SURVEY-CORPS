import { motion } from 'framer-motion'

/**
 * App section header — mirrors the landing page's eyebrow + accent-rule +
 * slab display heading so the in-app pages read as the same product
 * (round 3, item 4). Slides down on mount to match the landing motion language.
 */
export function SectionHeader({
  eyebrow,
  title,
  sub,
}: {
  eyebrow: string
  title: string
  sub?: string
}) {
  return (
    <motion.div
      className="mb-7"
      initial={{ opacity: 0, y: -14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="flex items-center gap-2.5">
        <span className="h-px w-6 flex-none bg-teal" />
        <span className="font-mono text-[0.7rem] font-semibold uppercase tracking-[0.22em] text-teal">
          {eyebrow}
        </span>
      </div>
      <h1 className="mt-3 font-display text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
        {title}
      </h1>
      <div className="mt-3 h-[3px] w-14 bg-teal" />
      {sub && <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">{sub}</p>}
    </motion.div>
  )
}
