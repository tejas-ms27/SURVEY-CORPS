import '@/styles/landing.css'

import { useNavigate } from 'react-router-dom'

import { Navbar } from '@/components/landing/Navbar'
import { Hero } from '@/components/landing/Hero'
import { Explainers } from '@/components/landing/Explainers'
import { Footer } from '@/components/landing/Footer'
import { useAppStore } from '@/store/useAppStore'

export function Landing() {
  const navigate = useNavigate()
  const enter = useAppStore((s) => s.enter)

  const openCase = () => {
    enter()
    navigate('/case')
  }

  return (
    <div className="sc">
      <Navbar />
      <main>
        <Hero onOpenCase={openCase} />
        <Explainers />
      </main>
      <Footer />
    </div>
  )
}
