import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Building2, CalendarClock, FileText, Info, Lightbulb } from 'lucide-react'
import ScoreRing from '../components/ScoreRing'
import SkillCard from '../components/SkillCard'
import { CategoryBars, StatusDonut } from '../components/Charts'
import { ErrorAlert, Spinner } from '../components/ui'
import { errorMessage, getAnalysis } from '../services/api'
import { formatDate, formatSimilarity } from '../utils/format'

const REC_GROUPS = [
  ['skill_gap', 'Skill gaps to work on'],
  ['review', 'Worth stating explicitly (if true)'],
  ['evidence', 'Strengthen existing evidence'],
  ['requirement', 'Other requirements in the posting'],
  ['resume_improvement', 'Resume improvements'],
]

export default function Results() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('matched')

  useEffect(() => {
    let live = true
    setData(null)
    getAnalysis(id).then((d) => live && setData(d)).catch((e) => live && setError(errorMessage(e)))
    return () => { live = false }
  }, [id])

  const categoryRows = useMemo(() => {
    if (!data) return []
    const rows = {}
    const add = (list, key) => list.forEach((s) => {
      const r = (rows[s.category] ||= { category: s.category, matched: 0, uncertain: 0, not_evidenced: 0 })
      r[key] += 1
    })
    add(data.matched_skills, 'matched'); add(data.uncertain_skills, 'uncertain'); add(data.not_evidenced_skills, 'not_evidenced')
    return Object.values(rows)
  }, [data])

  if (error) return <div className="mx-auto max-w-3xl px-4 py-16"><ErrorAlert>{error}</ErrorAlert><Link to="/history" className="btn-ghost mt-4">Back to history</Link></div>
  if (!data) return <div className="grid place-items-center py-32 text-slate-400"><Spinner size={24} label="Loading analysis..." /></div>

  const noReqs = data.requirements_total === 0
  const lists = { matched: data.matched_skills, uncertain: data.uncertain_skills, not_evidenced: data.not_evidenced_skills }
  const TABS = [
    ['matched', `Matched (${data.matched_skills.length})`],
    ['uncertain', `Uncertain (${data.uncertain_skills.length})`],
    ['not_evidenced', `Not evidenced (${data.not_evidenced_skills.length})`],
  ]
  const recs = REC_GROUPS.map(([k, label]) => [label, data.recommendations.filter((r) => r.category === k)]).filter(([, l]) => l.length)

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6">
      <header className="glass p-6">
        <p className="text-xs font-medium uppercase tracking-wider text-brand-cyan">Analysis #{data.id}</p>
        <h1 className="mt-1 font-display text-3xl font-bold text-white">{data.job_title}</h1>
        <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-400">
          {data.company_name && <span className="inline-flex items-center gap-1.5"><Building2 size={14} aria-hidden="true" />{data.company_name}</span>}
          <span className="inline-flex items-center gap-1.5"><FileText size={14} aria-hidden="true" />{data.resume_filename}</span>
          <span className="inline-flex items-center gap-1.5"><CalendarClock size={14} aria-hidden="true" />{formatDate(data.created_at)}</span>
        </div>
      </header>

      <section className="grid gap-5 md:grid-cols-2" aria-label="Metrics">
        <div className="glass-neon flex flex-col items-center gap-4 p-6 sm:flex-row">
          {noReqs ? <p className="text-slate-300">No requirements could be identified in this job description.</p> : <ScoreRing value={data.coverage_score} label="Requirement coverage" />}
          <div>
            <h2 className="font-semibold text-white">Requirement coverage</h2>
            <p className="mt-1 text-sm text-slate-400" data-testid="coverage-detail">
              {data.requirements_matched} of {data.requirements_total} identified requirements are supported by evidence in the resume.
            </p>
          </div>
        </div>
        <div className="glass p-6">
          <h2 className="font-semibold text-white">Semantic similarity</h2>
          <p className="mt-2 font-display text-4xl font-bold text-white" data-testid="similarity">{formatSimilarity(data.semantic_similarity)}</p>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10" aria-hidden="true">
            <div className="h-full rounded-full" style={{ width: `${Math.min(100, data.semantic_similarity * 100)}%`, backgroundImage: 'linear-gradient(90deg,#8b5cf6,#22d3ee)' }} />
          </div>
          <p className="mt-3 text-sm text-slate-400">Mean cosine similarity (0-1) between each requirement and its closest resume passage. It is an index, not a percentage or probability.</p>
        </div>
      </section>

      <p className="flex items-start gap-2 rounded-xl border border-amber-300/20 bg-amber-300/5 p-3 text-sm text-amber-100/90">
        <Info size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
        These results are not an official ATS score or a hiring probability. They show how well the text of your resume supports the requirements found in this posting.
      </p>

      {!noReqs && (
        <section className="grid gap-5 md:grid-cols-2" aria-label="Charts">
          <div className="glass p-5"><h2 className="mb-2 font-semibold text-white">Requirement status</h2>
            <StatusDonut matched={data.matched_skills.length} uncertain={data.uncertain_skills.length} notEvidenced={data.not_evidenced_skills.length} /></div>
          <div className="glass p-5"><h2 className="mb-2 font-semibold text-white">Skill gap by category</h2><CategoryBars rows={categoryRows} /></div>
        </section>
      )}

      {!noReqs && (
        <section aria-label="Requirements">
          <h2 className="font-display text-2xl font-bold text-white">Requirements &amp; evidence</h2>
          <div role="tablist" className="mt-4 flex flex-wrap gap-2">
            {TABS.map(([k, label]) => (
              <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${tab === k ? 'bg-brand-purple text-white' : 'bg-white/5 text-slate-300 hover:bg-white/10'}`}>{label}</button>
            ))}
          </div>
          <ul className="mt-4 grid gap-3 lg:grid-cols-2" role="tabpanel">
            {lists[tab].map((s, i) => <SkillCard key={`${s.skill_name}-${i}`} item={s} />)}
            {lists[tab].length === 0 && <li className="text-sm text-slate-400">Nothing in this group.</li>}
          </ul>
        </section>
      )}

      <section aria-label="Recommendations">
        <h2 className="flex items-center gap-2 font-display text-2xl font-bold text-white"><Lightbulb className="text-brand-cyan" aria-hidden="true" /> Recommendations</h2>
        <div className="mt-4 grid gap-5 lg:grid-cols-2">
          {recs.map(([label, items]) => (
            <div key={label} className="glass p-5">
              <h3 className="font-semibold text-white">{label}</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-300">{items.map((r, i) => <li key={i}>{r.message}</li>)}</ul>
            </div>
          ))}
          {recs.length === 0 && <p className="text-sm text-slate-400">No recommendations for this analysis.</p>}
        </div>
        <p className="mt-3 text-xs text-slate-500">Recommendations come from a curated, rule-based catalog. Only add experience you genuinely have.</p>
      </section>

      <section className="glass p-6" aria-label="How scores are calculated">
        <h2 className="font-display text-xl font-bold text-white">How these scores are calculated</h2>
        <div className="mt-3 space-y-3 text-sm text-slate-300">
          <p><strong className="text-white">Requirement coverage</strong> = supported requirements / total identified requirements x 100. Requirements are the skills found in the job description plus requirement statements. A skill counts as supported only when it is explicitly mentioned (and not negated) in the resume. Statements need high embedding similarity plus a shared key term.</p>
          <p><strong className="text-white">Semantic similarity</strong> = the mean, over all requirements, of the highest cosine similarity between the requirement and any resume passage, using the local <code>all-MiniLM-L6-v2</code> model.</p>
          <p><strong className="text-white">Limitations:</strong> thresholds are unvalidated defaults; the skill catalog is finite; similar-sounding text can be misleading; scanned PDFs are not supported. "Not evidenced" means the resume text does not show it, not that you lack the skill. Model: <span className="text-slate-400">{data.model_version}</span></p>
        </div>
      </section>

      <div className="flex gap-3"><Link to="/analyze" className="btn-primary">New analysis</Link><Link to="/history" className="btn-ghost">History</Link></div>
    </motion.div>
  )
}
