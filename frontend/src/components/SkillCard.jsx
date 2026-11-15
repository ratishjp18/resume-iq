import { Quote } from 'lucide-react'
import { StatusBadge } from './ui'
import { formatSimilarity } from '../utils/format'

export default function SkillCard({ item }) {
  return (
    <li className="glass p-4" data-testid="skill-card">
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="font-semibold text-white">{item.skill_name}</h4>
        <StatusBadge status={item.status} />
        <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-slate-400">{item.category}</span>
        {item.evidence_strength === 'listed' && (
          <span className="rounded-full bg-amber-400/10 px-2 py-0.5 text-xs text-amber-300">Listed only</span>
        )}
        {item.similarity_score != null && (
          <span className="ml-auto text-xs text-slate-500" title="Cosine similarity of the requirement and the closest resume passage (not a probability)">
            similarity {formatSimilarity(item.similarity_score)}
          </span>
        )}
      </div>
      {item.resume_evidence ? (
        <blockquote className="mt-3 flex gap-2 border-l-2 border-brand-purple/50 pl-3 text-sm text-slate-300">
          <Quote size={14} className="mt-1 shrink-0 text-brand-purple" aria-hidden="true" />
          <span>{item.resume_evidence}</span>
        </blockquote>
      ) : (
        <p className="mt-3 text-sm text-slate-400">Not evidenced in resume.</p>
      )}
      {item.note && <p className="mt-2 text-xs text-slate-400">{item.note}</p>}
    </li>
  )
}
