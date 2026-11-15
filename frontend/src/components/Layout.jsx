import { Link, NavLink, Outlet } from 'react-router-dom'
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

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-white/5 bg-ink-900/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Logo />
          <nav className="flex items-center gap-1" aria-label="Main">
            <NavLink to="/analyze" className={navCls}>Analyze</NavLink>
            <NavLink to="/history" className={navCls}>History</NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-white/5 py-8 text-center text-xs text-slate-500">
        <p>ResumeIQ - runs locally. Your resume never leaves your machine. Results are explainable heuristics, not an ATS score or hiring probability.</p>
      </footer>
    </div>
  )
}
