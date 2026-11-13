import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ChevronDown, ChevronUp, Sparkles } from 'lucide-react'
import FileDropzone from '../components/FileDropzone'
import { ErrorAlert, Spinner } from '../components/ui'
import { createAnalysis, createJob, deleteResume, errorMessage, uploadResume } from '../services/api'
import { validateFile, validateJob } from '../utils/validation'

const STEPS = ['Saving job description', 'Extracting skills & running the embedding model', 'Scoring and building recommendations']

export default function Analyze() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [resume, setResume] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [fileError, setFileError] = useState('')
  const [showText, setShowText] = useState(false)

  const [title, setTitle] = useState('')
  const [company, setCompany] = useState('')
  const [description, setDescription] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})

  const [running, setRunning] = useState(false)
  const [step, setStep] = useState(0)
  const [error, setError] = useState('')

  async function handleFile(f) {
    setFileError('')
    setError('')
    const problem = validateFile(f)
    if (problem) return setFileError(problem)
    setFile(f)
    setUploading(true)
    try {
      setResume(await uploadResume(f))
    } catch (err) {
      setFile(null)
      setFileError(errorMessage(err))
    } finally {
      setUploading(false)
    }
  }

  async function clearFile() {
    const id = resume?.id
    setFile(null)
    setResume(null)
    setShowText(false)
    if (id) deleteResume(id).catch(() => {}) // do not keep resume data the user removed
  }

  async function submit(e) {
    e.preventDefault()
    setError('')
    const errors = validateJob({ title, description })
    setFieldErrors(errors)
    if (!resume) return setFileError('Upload a resume first.')
    if (Object.keys(errors).length) return
    setRunning(true)
    setStep(0)
    try {
      const job = await createJob({ title: title.trim(), company_name: company.trim() || null, description_text: description.trim() })
      setStep(1)
      const timer = setTimeout(() => setStep(2), 2500)
      try {
        const analysis = await createAnalysis(resume.id, job.id)
        navigate(`/analysis/${analysis.id}`)
      } finally {
        clearTimeout(timer)
      }
    } catch (err) {
      setError(errorMessage(err))
      setRunning(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <h1 className="font-display text-3xl font-bold text-white">Analyze your resume</h1>
      <p className="mt-2 text-slate-400">Upload a resume and paste the job description you are targeting.</p>

      <form onSubmit={submit} className="mt-8 space-y-8" noValidate>
        <section aria-labelledby="s1" className="space-y-3">
          <h2 id="s1" className="font-semibold text-white">1. Resume</h2>
          <FileDropzone file={file} error={fileError} disabled={uploading || running} onFile={handleFile} onClear={clearFile} />
          {uploading && <p className="text-sm text-slate-400"><Spinner label="Uploading and extracting text..." /></p>}
          <ErrorAlert>{fileError}</ErrorAlert>
          {resume && (
            <div className="glass p-4" data-testid="resume-preview">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm text-slate-300">
                  Extracted <strong className="text-white">{resume.word_count.toLocaleString()}</strong> words from <span className="uppercase">{resume.file_type}</span>
                </p>
                <button type="button" className="btn-ghost !px-3 !py-1.5" onClick={() => setShowText((s) => !s)} aria-expanded={showText}>
                  {showText ? <ChevronUp size={14} /> : <ChevronDown size={14} />} {showText ? 'Hide' : 'Preview'} text
                </button>
              </div>
              {showText && (
                <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-ink-950/70 p-3 text-xs text-slate-300">{resume.extracted_text}</pre>
              )}
            </div>
          )}
        </section>

        <section aria-labelledby="s2" className="space-y-4">
          <h2 id="s2" className="font-semibold text-white">2. Job details</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="title" className="label">Job title *</label>
              <input id="title" className="input" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Backend Engineer" aria-invalid={!!fieldErrors.title} aria-describedby={fieldErrors.title ? 'title-err' : undefined} />
              {fieldErrors.title && <p id="title-err" className="mt-1 text-xs text-rose-300">{fieldErrors.title}</p>}
            </div>
            <div>
              <label htmlFor="company" className="label">Company (optional)</label>
              <input id="company" className="input" value={company} maxLength={200} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Acme Corp" />
            </div>
          </div>
          <div>
            <label htmlFor="jd" className="label">Job description *</label>
            <textarea id="jd" rows={10} className="input resize-y" value={description} onChange={(e) => setDescription(e.target.value)}
              placeholder="Paste the full job description here..." aria-invalid={!!fieldErrors.description}
              aria-describedby={fieldErrors.description ? 'jd-err' : undefined} />
            <div className="mt-1 flex justify-between text-xs">
              <span id="jd-err" className="text-rose-300">{fieldErrors.description}</span>
              <span className="text-slate-500">{description.length.toLocaleString()} / 30,000</span>
            </div>
          </div>
        </section>

        <ErrorAlert onDismiss={() => setError('')}>{error}</ErrorAlert>

        <button type="submit" className="btn-primary w-full py-3 sm:w-auto" disabled={running || uploading}>
          {running ? <Spinner label="Analyzing..." /> : <><Sparkles size={16} aria-hidden="true" /> Analyze</>}
        </button>
      </form>

      {running && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="fixed inset-0 z-40 grid place-items-center bg-ink-950/80 p-4 backdrop-blur-sm" role="status" aria-live="polite" data-testid="processing">
          <div className="glass-neon w-full max-w-md bg-ink-800 p-8 text-center">
            <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-white/10 border-t-brand-cyan" aria-hidden="true" />
            <h2 className="mt-5 font-display text-xl font-semibold text-white">Analyzing your resume</h2>
            <p className="mt-2 text-sm text-slate-400">{STEPS[step]}...</p>
            <p className="mt-4 text-xs text-slate-500">The first analysis can take longer while the model loads.</p>
          </div>
        </motion.div>
      )}
    </div>
  )
}
