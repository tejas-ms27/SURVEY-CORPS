import { useEffect, useState } from 'react'

import logoUrl from '@/assets/logo.png'

const scrollToSection = (id: string) => {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const LINKS = [
  { label: 'Extraction', id: 'extraction-section' },
  { label: 'Analysis', id: 'analysis-section' },
  { label: 'Chatbot', id: 'chatbot-section' },
]

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header className={`sc-nav${scrolled ? ' scrolled' : ''}`}>
      <div className="sc-wrap sc-nav-inner">
        <a
          href="/"
          className="sc-brand"
          aria-label="Survey Corps home"
          onClick={(e) => {
            if (window.location.pathname === '/') {
              e.preventDefault()
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }
          }}
        >
          <img src={logoUrl} className="sc-logo" alt="Survey Corps" />
          SURVEY&nbsp;CORPS
        </a>
        <nav className="sc-nav-links">
          {LINKS.map((l) => (
            <button key={l.id} type="button" className="sc-nav-link" onClick={() => scrollToSection(l.id)}>
              {l.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  )
}
