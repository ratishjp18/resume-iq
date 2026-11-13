import { useEffect, useRef } from 'react'
import { AlertCircle, CheckCircle2, HelpCircle, Loader2, XCircle } from 'lucide-react'
import { STATUS_META } from '../utils/format'

export function Spinner({ size = 18, label }) {
  return (
    <span className="inline-flex items-center gap-2" role="status">
      <Loader2 size={size} className="animate-spin" aria-hidden="true" />
      {label && <span>{label}</span>}
    </span>
  )
}

export function ErrorAlert({ children, onDismiss }) {
  if (!children) return null
  return (
    <div role="alert" className="flex items-start gap-3 rounded-xl border border-rose-400/30 bg-rose-500/10 p-3 text-sm text-rose-100">
      <AlertCircle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
      <p className="flex-1">{children}</p>
      {onDismiss && (
        <button onClick={onDismiss} className="text-rose-200/70 hover:text-white" aria-label="Dismiss error">
          <XCircle size={16} />
        </button>
      )}
    </div>
  )
}

const STATUS_ICON = { matched: CheckCircle2, uncertain: HelpCircle, not_evidenced: XCircle }

/** Status is conveyed by icon + text, not by colour alone. */
export function StatusBadge({ status }) {
  const meta = STATUS_META[status]
  const Icon = STATUS_ICON[status]
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold"
      style={{ color: meta.color, borderColor: `${meta.color}55`, background: `${meta.color}14` }}
    >
      <Icon size={12} aria-hidden="true" /> {meta.label}
    </span>
  )
}

export function ConfirmDialog({ open, title, message, confirmLabel = 'Delete', busy, onConfirm, onCancel }) {
  const cancelRef = useRef(null)
  useEffect(() => {
    if (!open) return undefined
    cancelRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onCancel()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onCancel])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm">
      <div role="dialog" aria-modal="true" aria-labelledby="confirm-title" className="glass-neon w-full max-w-md bg-ink-800 p-6">
        <h2 id="confirm-title" className="font-display text-lg font-semibold text-white">{title}</h2>
        <p className="mt-2 text-sm text-slate-300">{message}</p>
        <div className="mt-6 flex justify-end gap-3">
          <button ref={cancelRef} className="btn-ghost" onClick={onCancel} disabled={busy}>Cancel</button>
          <button className="btn-danger" onClick={onConfirm} disabled={busy}>
            {busy ? <Spinner size={14} /> : null}{confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
