export function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

export function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export const formatPercent = (n) => `${Number(n).toFixed(1).replace(/\.0$/, '')}%`
export const formatSimilarity = (n) => Number(n).toFixed(2)

export const STATUS_META = {
  matched: { label: 'Matched', color: '#34d399' },
  uncertain: { label: 'Uncertain', color: '#fbbf24' },
  not_evidenced: { label: 'Not evidenced', color: '#fb7185' },
}
