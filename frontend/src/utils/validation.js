export const MAX_FILE_BYTES = 5 * 1024 * 1024
export const ALLOWED_EXTENSIONS = ['.pdf', '.docx']

export function validateFile(file) {
  if (!file) return 'Please choose a resume file.'
  const name = file.name.toLowerCase()
  if (!ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext))) {
    return 'Unsupported file type. Please upload a PDF or DOCX resume.'
  }
  if (file.size === 0) return 'The selected file is empty.'
  if (file.size > MAX_FILE_BYTES) return 'File is too large. The maximum size is 5 MB.'
  return null
}

export function validateJob({ title, description }) {
  const errors = {}
  if (!title || title.trim().length < 2) errors.title = 'Enter a job title (at least 2 characters).'
  if (!description || description.trim().length < 30) {
    errors.description = 'Paste the job description (at least 30 characters).'
  } else if (description.length > 30000) {
    errors.description = 'The job description is too long (maximum 30,000 characters).'
  }
  return errors
}
