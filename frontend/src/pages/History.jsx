import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Eye, Search, Trash2, UserX } from 'lucide-react'
import { ConfirmDialog, ErrorAlert, Spinner } from '../components/ui'
import { useDebounce } from '../hooks/useDebounce'
import { deleteAnalysis, deleteResume, errorMessage, listAnalyses } from '../services/api'
import { formatDate, formatPercent, formatSimilarity } from '../utils/format'

const SORTS = [
  ['date:desc', 'Newest first'],
  ['date:asc', 'Oldest first'],
  ['coverage:desc', 'Coverage (high to low)'],
  ['coverage:asc', 'Coverage (low to high)'],
  ['job_title:asc', 'Job title (A-Z)'],
]

export default function History() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [q, setQ] = useState('')
  const [sort, setSort] = useState('date:desc')
  const [pending, setPending] = useState(null) // { kind: 'analysis' | 'resume', item }
  const [busy, setBusy] = useState(false)
  const dq = useDebounce(q)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [sort_by, order] = sort.split(':')
      const data = await listAnalyses({ q: dq || undefined, sort_by, order })
      setItems(data.items)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setLoading(false)
    }
  }, [dq, sort])

  useEffect(() => { load() }, [load])

  async function confirmDelete() {
    setBusy(true)
    try {
      if (pending.kind === 'analysis') await deleteAnalysis(pending.item.id)
      else await deleteResume(pending.item.resume_id)
      setPending(null)
      await load()
    } catch (e) {
      setError(errorMessage(e))
      setPending(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <h1 className="font-display text-3xl font-bold text-white">Analysis history</h1>
      <p className="mt-2 text-slate-400">Stored locally in SQLite on this machine.</p>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" aria-hidden="true" />
          <input className="input !pl-9" placeholder="Search job title or company" aria-label="Search analyses" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <select className="input sm:w-56" aria-label="Sort analyses" value={sort} onChange={(e) => setSort(e.target.value)}>
          {SORTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>

      <div className="mt-4"><ErrorAlert onDismiss={() => setError('')}>{error}</ErrorAlert></div>

      {loading ? (
        <div className="py-20 text-center text-slate-400"><Spinner size={22} label="Loading history..." /></div>
      ) : items.length === 0 ? (
        <div className="glass mt-6 p-10 text-center">
          <p className="text-slate-300">{dq ? 'No analyses match your search.' : 'No analyses yet.'}</p>
          {!dq && <Link to="/analyze" className="btn-primary mt-4">Analyze a resume</Link>}
        </div>
      ) : (
        <ul className="mt-6 space-y-3">
          {items.map((a) => (
            <li key={a.id} className="glass flex flex-col gap-4 p-4 sm:flex-row sm:items-center" data-testid="history-item">
              <div className="min-w-0 flex-1">
                <h2 className="truncate font-semibold text-white">{a.job_title}</h2>
                <p className="truncate text-sm text-slate-400">{a.company_name || 'No company'} - {a.resume_filename}</p>
                <p className="text-xs text-slate-500">{formatDate(a.created_at)}</p>
              </div>
              <dl className="flex gap-6 text-sm">
                <div><dt className="text-xs text-slate-500">Coverage</dt><dd className="font-display text-lg font-bold text-white">{formatPercent(a.coverage_score)}</dd></div>
                <div><dt className="text-xs text-slate-500">Similarity</dt><dd className="font-display text-lg font-bold text-white">{formatSimilarity(a.semantic_similarity)}</dd></div>
              </dl>
              <div className="flex flex-wrap gap-2">
                <Link to={`/analysis/${a.id}`} className="btn-ghost !px-3 !py-1.5"><Eye size={14} aria-hidden="true" /> View</Link>
                <button className="btn-danger !px-3 !py-1.5" onClick={() => setPending({ kind: 'analysis', item: a })} aria-label={`Delete analysis for ${a.job_title}`}>
                  <Trash2 size={14} aria-hidden="true" /> Delete
                </button>
                <button className="btn-danger !px-3 !py-1.5" onClick={() => setPending({ kind: 'resume', item: a })} aria-label={`Delete saved resume data for ${a.job_title}`}>
                  <UserX size={14} aria-hidden="true" /> Delete resume
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={!!pending}
        busy={busy}
        title={pending?.kind === 'resume' ? 'Delete saved resume data?' : 'Delete this analysis?'}
        message={pending?.kind === 'resume'
          ? `This permanently deletes the saved resume "${pending?.item.resume_filename}" and every analysis created from it.`
          : 'This permanently deletes the analysis results. The resume stays saved.'}
        confirmLabel={pending?.kind === 'resume' ? 'Delete resume data' : 'Delete analysis'}
        onConfirm={confirmDelete}
        onCancel={() => !busy && setPending(null)}
      />
    </div>
  )
}
