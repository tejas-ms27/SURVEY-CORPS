import { motion } from 'framer-motion'

import { Marquee } from '@/components/landing/Explainers'

export function Hero({ onOpenCase }: { onOpenCase: () => void }) {
  return (
    <section className="sc-hero">
      {/* Looping background animation. Muted + playsInline so it autoplays on
          all browsers; object-fit: cover handles any resolution. Sits behind
          the content (see .sc-hero-video / .sc-hero-inner z-index in CSS). */}
      <video
        className="sc-hero-video"
        src="/background_animation.mp4"
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
        aria-hidden="true"
      />
      <div className="sc-hero-scrim" aria-hidden="true" />

      <motion.div
        className="sc-hero-inner"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      >
        <h1>SURVEY&nbsp;CORPS</h1>
        <div className="rule" />

        <p className="sc-hero-sub">
          A forensic engine for financial-crime investigators. Feed it inconsistent bank statements
          across banks, formats and languages — it reconstructs one reconciled ledger, flags what
          doesn&apos;t add up, and lets you interrogate the whole case in plain language.
        </p>

        <div className="sc-hero-cta">
          <motion.button
            className="sc-btn-white"
            type="button"
            onClick={onOpenCase}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.97 }}
            transition={{ duration: 0.15 }}
          >
            ▸&nbsp;&nbsp;Open a Case File
          </motion.button>
        </div>
      </motion.div>

      {/* Ticker lives inside the hero so it's above the fold on load (item 1). */}
      <Marquee />
    </section>
  )
}
