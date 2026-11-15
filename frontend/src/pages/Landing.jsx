import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, BarChart3, Brain, Cpu, FileSearch, Lightbulb, Lock, Search, ShieldCheck, Upload } from 'lucide-react'

const fade = (i = 0) => ({
  initial: { opacity: 0, y: 18 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.5, delay: i * 0.08 },
})

const FEATURES = [
  { icon: FileSearch, title: 'Evidence-based matching', text: 'Every requirement is linked to the resume passage that supports it, so you can see exactly why it was matched.' },
  { icon: Brain, title: 'Semantic understanding', text: 'Sentence embeddings compare meaning, not just keywords - combined with explicit skill detection to avoid false matches.' },
  { icon: BarChart3, title: 'Skill gap analysis', text: 'See matched, uncertain and not-evidenced skills by category, with charts and clear metrics.' },
  { icon: Lightbulb, title: 'Practical recommendations', text: 'Deterministic, curated suggestions for closing gaps. Nothing is invented on your behalf.' },
  { icon: Lock, title: 'Private by design', text: 'Everything runs on your machine. No paid APIs, no uploads to third parties, delete your data anytime.' },
  { icon: ShieldCheck, title: 'Honest scoring', text: 'Coverage and similarity are explained and caveated. This is not an ATS score or a hiring prediction.' },
]
const STEPS = [
  { icon: Upload, title: 'Upload your resume', text: 'PDF or DOCX, parsed locally in seconds.' },
  { icon: Search, title: 'Add a job description', text: 'Paste the posting you are targeting.' },
  { icon: BarChart3, title: 'Review your analysis', text: 'Explore coverage, evidence, gaps and next steps.' },
]
const TECH = ['React + Vite', 'Tailwind CSS', 'FastAPI', 'SQLAlchemy + SQLite', 'Sentence Transformers', 'all-MiniLM-L6-v2', 'scikit-learn', 'PyMuPDF', 'python-docx']

export default function Landing() {
  return (
    <div>
      <section className="mx-auto max-w-6xl px-4 pb-20 pt-20 text-center sm:px-6 sm:pt-28">
        <motion.span {...fade()} className="inline-flex items-center gap-2 rounded-full border border-brand-cyan/30 bg-brand-cyan/10 px-3 py-1 text-xs font-medium text-cyan-200">
          <Cpu size={14} aria-hidden="true" /> 100% local AI - no paid APIs
        </motion.span>
        <motion.h1 {...fade(1)} className="mx-auto mt-6 max-w-3xl font-display text-4xl font-bold leading-tight text-white sm:text-6xl">
          Understand Your Resume.<br />
          <span className="gradient-text-animated">Discover Your Skill Gaps.</span>
        </motion.h1>
        <motion.p {...fade(2)} className="mx-auto mt-6 max-w-2xl text-lg text-slate-400">
          ResumeIQ compares your resume with a job description using NLP and sentence embeddings, shows the evidence behind
          every match, and helps you prepare for your next opportunity.
        </motion.p>
        <motion.div {...fade(3)} className="mt-10 flex flex-wrap justify-center gap-3">
          <Link to="/analyze" className="btn-primary btn-shine px-7 py-3 text-base">Analyze My Resume <ArrowRight size={18} aria-hidden="true" /></Link>
          <Link to="/history" className="btn-ghost px-7 py-3 text-base">View History</Link>
        </motion.div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6" aria-labelledby="features">
        <h2 id="features" className="text-center font-display text-3xl font-bold text-white">Built to be useful, and honest</h2>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div key={f.title} {...fade(i % 3)} whileHover={{ y: -6 }} className="glass card-hover p-6">
              <f.icon className="animate-float text-brand-cyan" style={{ animationDelay: `${i * 0.4}s` }} aria-hidden="true" />
              <h3 className="mt-4 font-semibold text-white">{f.title}</h3>
              <p className="mt-2 text-sm text-slate-400">{f.text}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6" aria-labelledby="how">
        <h2 id="how" className="text-center font-display text-3xl font-bold text-white">How it works</h2>
        <ol className="mt-10 grid gap-5 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <motion.li key={s.title} {...fade(i)} whileHover={{ y: -6 }} className="glass card-hover relative p-6">
              <span className="absolute right-5 top-4 font-display text-5xl font-bold text-white/5">{i + 1}</span>
              <s.icon className="text-brand-purple" aria-hidden="true" />
              <h3 className="mt-4 font-semibold text-white">{s.title}</h3>
              <p className="mt-2 text-sm text-slate-400">{s.text}</p>
            </motion.li>
          ))}
        </ol>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12 text-center sm:px-6" aria-labelledby="tech">
        <h2 id="tech" className="font-display text-2xl font-bold text-white">Technology highlights</h2>
        <div className="marquee-mask mt-6 overflow-hidden">
          <div className="flex w-max animate-marquee gap-2 hover:[animation-play-state:paused]">
            {[...TECH, ...TECH].map((t, i) => (
              <span key={`${t}-${i}`} aria-hidden={i >= TECH.length ? 'true' : undefined} className="whitespace-nowrap rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-sm text-slate-300">{t}</span>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
