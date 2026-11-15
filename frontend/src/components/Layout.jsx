import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { motion, useScroll, useSpring } from 'framer-motion'
import { Sparkles } from 'lucide-react'

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-display text-lg font-bold text-white" aria-label="ResumeIQ home">
      <span className="grid h-8 w-8 place-items-center rounded-lg" style={{ backgroundImage: 'linear-gradient(135deg,#8b5cf6,#22d3ee)' }}>
        <Sparkles size={16} className="text-ink-900" aria-hidden="true" />
      </span>
      Resume<span className="gradient-text">IQ</span>
    </Link>
  )
}

const navCls = ({ isActive }) =>
  `rounded-lg px-3 py-1.5 text-sm font-medium transition ${isActive ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'}`

function Background() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div className="absolute -left-32 top-10 h-96 w-96 animate-drift rounded-full bg-brand-purple/20 blur-3xl" />
      <div className="absolute -right-24 top-1/3 h-[28rem] w-[28rem] animate-drift-rev rounded-full bg-brand-cyan/15 blur-3xl" />
      <div className="absolute bottom-0 left-1/3 h-80 w-80 animate-drift rounded-full bg-fuchsia-500/10 blur-3xl" />
    </div>
  )
}

export default function Layout() {
  const { pathname } = useLocation()
  const { scrollYProgress } = useScroll()
  const scaleX = useSpring(scrollYProgress, { stiffness: 120, damping: 24, restDelta: 0.001 })
  return (
    <div className="flex min-h-screen flex-col">
      <Background />
      <motion.div style={{ scaleX }} className="fixed inset-x-0 top-0 z-50 h-0.5 origin-left bg-gradient-to-r from-brand-purple to-brand-cyan" aria-hidden="true" />
      <header className="sticky top-0 z-30 border-b border-white/5 bg-ink-900/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Logo />
          <nav className="flex items-center gap-1" aria-label="Main">
            <NavLink to="/analyze" className={navCls}>Analyze</NavLink>
            <NavLink to="/history" className={navCls}>History</NavLink>
          </nav>
        </div>
      </header>
      <motion.main key={pathname} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, ease: 'easeOut' }} className="flex-1">
        <Outlet />
      </motion.main>
      <footer className="border-t border-white/5 py-8 text-center text-xs text-slate-500">
        <p>ResumeIQ - runs locally. Your resume never leaves your machine. Results are explainable heuristics, not an ATS score or hiring probability.</p>
      </footer>
    </div>
  )
}
