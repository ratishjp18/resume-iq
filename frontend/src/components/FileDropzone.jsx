import { useRef, useState } from 'react'
import { FileText, UploadCloud, X } from 'lucide-react'
import { formatBytes } from '../utils/format'

export default function FileDropzone({ file, disabled, error, onFile, onClear }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const pick = (f) => f && onFile(f)

  if (file) {
    return (
      <div className="glass flex items-center gap-3 p-4">
        <FileText className="text-brand-cyan" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-white" data-testid="file-name">{file.name}</p>
          <p className="text-xs text-slate-400" data-testid="file-size">{formatBytes(file.size)}</p>
        </div>
        <button className="btn-ghost !px-3 !py-1.5" onClick={onClear} disabled={disabled} aria-label="Remove file">
          <X size={14} /> Remove
        </button>
      </div>
    )
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload resume. Drag and drop a PDF or DOCX file here, or press Enter to browse."
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), inputRef.current?.click())}
        onDragOver={(e) => (e.preventDefault(), setDragging(true))}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          pick(e.dataTransfer.files?.[0])
        }}
        className={`glass cursor-pointer border-dashed p-8 text-center transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cyan ${
          dragging ? 'border-brand-cyan bg-brand-cyan/10' : 'hover:border-brand-purple/60'
        } ${error ? 'border-rose-400/50' : ''}`}
      >
        <UploadCloud className="mx-auto mb-3 text-brand-purple" size={36} aria-hidden="true" />
        <p className="font-medium text-white">Drag &amp; drop your resume</p>
        <p className="mt-1 text-sm text-slate-400">or click to browse - PDF or DOCX, up to 5 MB</p>
        <input
          ref={inputRef}
          type="file"
          data-testid="file-input"
          className="sr-only"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={(e) => {
            pick(e.target.files?.[0])
            e.target.value = ''
          }}
          tabIndex={-1}
        />
      </div>
    </div>
  )
}
