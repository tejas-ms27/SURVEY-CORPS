import type { ReactNode } from 'react'
import { motion } from 'framer-motion'

/* Scroll-triggered reveal: each section starts offset *above* its resting
   spot and slides down into view as it enters the viewport (round 3, item 2).
   Kept quick (~0.55s) so it never feels sluggish while scrolling. */
function Reveal({ children, className, id }: { children: ReactNode; className?: string; id?: string }) {
  return (
    <motion.section
      id={id}
      className={className}
      initial={{ opacity: 0, y: -48 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.section>
  )
}

/* Feature card with a Framer "pop" on hover — lifts + scales, while the CSS
   (see landing.css) brightens the text (round 3, item 1). */
function FeatureCard({ ic, h, p }: { ic: string; h: string; p: string }) {
  return (
    <motion.div
      className="sc-card"
      whileHover={{ scale: 1.045, y: -6 }}
      transition={{ type: 'spring', stiffness: 320, damping: 20 }}
    >
      <div className="ic">{ic}</div>
      <h3>{h}</h3>
      <p>{p}</p>
    </motion.div>
  )
}

/* ------------------------------------------------------------------ */
/* Sliding marquee bar                                                 */
/* Content is a plain editable array — wording is a content decision.  */
/* ------------------------------------------------------------------ */
const MARQUEE_ITEMS = [
  'Multi-bank extraction',
  'Digital + scanned statements',
  'Cross-account fraud detection',
  'Structuring & smurfing alerts',
  'Bilingual chatbot — EN / ಕನ್ನಡ',
  'Citation-backed answers',
  'Exact arithmetic, not guesses',
  'Court-ready reporting',
]

export function Marquee() {
  return (
    <div className="sc-marquee" aria-hidden>
      <div className="sc-marquee-track">
        {[0, 1].map((dup) => (
          <div className="sc-marquee-item" key={dup}>
            {MARQUEE_ITEMS.map((item) => <span key={item}>{item}</span>)}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Extraction explainer — WHITE background (deliberate contrast break) */
/* Accents pull from the indigo palette, verified for white bg.        */
/* ------------------------------------------------------------------ */
const EXTRACTION_CARDS = [
  { ic: '01', h: 'Every bank, every format', p: 'Ingests statements from any bank — digital PDFs, scanned scans, Excel and CSV — without a per-bank template.' },
  { ic: '02', h: 'Tiered, not lossy', p: 'Deterministic parse first, schema re-parse next, full LLM read only where needed. Nothing is summarised away.' },
  { ic: '03', h: 'Structured output', p: 'Emits clean, flagged and duplicate rows as one normalised ledger, ready for analysis and reporting.' },
]

function Extraction() {
  return (
    <Reveal id="extraction-section" className="sc-explainer sc-white">
      <div className="sc-wrap">
        <span className="sc-eyebrow">Extraction</span>
        <h2>Automated Extraction</h2>
        <p className="lead">
          Investigators drown in statements that never match — different banks, layouts, languages
          and scan quality. Survey Corps reads all of them and reconstructs a single, reconciled
          ledger you can actually work with.
        </p>
        <div className="sc-cards">
          {EXTRACTION_CARDS.map((c) => (
            <FeatureCard key={c.ic} ic={c.ic} h={c.h} p={c.p} />
          ))}
        </div>
      </div>
    </Reveal>
  )
}

/* ------------------------------------------------------------------ */
/* Analysis explainer — dark                                           */
/* ------------------------------------------------------------------ */
const ANALYSIS_CARDS = [
  { ic: 'STRUCTURING', h: 'Pattern detection', p: 'Surfaces structuring and smurfing — deposits split just under reporting thresholds — across time and accounts.' },
  { ic: 'GRAPH', h: 'Cross-account graphs', p: 'Traces money between parties and visualises the flow, exposing round-tripping and layered transfers.' },
  { ic: 'EXACT', h: 'Exact arithmetic', p: 'Balances and totals are computed, not estimated by a model — every figure ties out and is auditable.' },
]

function Analysis() {
  return (
    <Reveal id="analysis-section" className="sc-explainer sc-dark">
      <div className="sc-wrap">
        <span className="sc-eyebrow">Analysis</span>
        <h2>See the whole case</h2>
        <p className="lead">
          Once the ledger is reconstructed, Survey Corps analyses it end to end — detecting fraud
          patterns, mapping how money moves between parties, and aggregating everything into a
          court-ready report.
        </p>
        <div className="sc-cards">
          {ANALYSIS_CARDS.map((c) => (
            <FeatureCard key={c.ic} ic={c.ic} h={c.h} p={c.p} />
          ))}
        </div>
      </div>
    </Reveal>
  )
}

/* ------------------------------------------------------------------ */
/* Chatbot explainer — WHITE, with animated chat mock flourish         */
/* The chat mock stays a dark card (deliberate contrast) so its         */
/* near-white bubbles remain legible; surrounding copy uses .sc-white.  */
/* ------------------------------------------------------------------ */
function Chatbot() {
  return (
    <Reveal id="chatbot-section" className="sc-explainer sc-white">
      <div className="sc-wrap">
        <div className="sc-chat-layout">
          <div>
            <span className="sc-eyebrow">Chatbot</span>
            <h2>Interrogate the evidence</h2>
            <p className="lead">
              Ask the case questions in plain English or Kannada. Answers are citation-backed and
              come from structured lookups and semantic retrieval together — with exact-ID lookup
              and interactive transaction graphs when you need to follow the money.
            </p>
          </div>

          <motion.div
            className="sc-chat"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="sc-chat-head"><span className="live" />case_qa · bilingual</div>
            <div className="sc-bubble user">Who received the largest transfer from account ····4471?</div>
            <div className="sc-bubble bot">
              ₹4,50,000 was transferred to <b>Party&nbsp;B</b> on 12 Mar 2024.
              <span className="cite">↳ txn #10482 · stmt p.7 · verified</span>
            </div>
            <div className="sc-typing" aria-label="typing"><i /><i /><i /></div>
          </motion.div>
        </div>
      </div>
    </Reveal>
  )
}

export function Explainers() {
  return (
    <>
      <Extraction />
      <Analysis />
      <Chatbot />
    </>
  )
}
