import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001',
  timeout: 120000, // first analysis may include model warm-up on CPU
})

export function errorMessage(err) {
  if (err?.response) {
    const e = err.response.data?.error
    if (e?.details?.length) {
      return `${e.message} ${e.details.map((d) => `${d.field}: ${d.message}`).join('; ')}`
    }
    return e?.message || `Request failed (${err.response.status}).`
  }
  if (err?.code === 'ECONNABORTED') return 'The request timed out. Please try again.'
  return 'Cannot reach the ResumeIQ backend. Make sure it is running on http://localhost:8001.'
}

export const uploadResume = (file) => {
  const form = new FormData()
  form.append('file', file)
  return client.post('/api/resumes', form).then((r) => r.data)
}
export const deleteResume = (id) => client.delete(`/api/resumes/${id}`)
export const createJob = (payload) => client.post('/api/jobs', payload).then((r) => r.data)
export const createAnalysis = (resume_id, job_id) =>
  client.post('/api/analyses', { resume_id, job_id }).then((r) => r.data)
export const getAnalysis = (id) => client.get(`/api/analyses/${id}`).then((r) => r.data)
export const listAnalyses = (params) => client.get('/api/analyses', { params }).then((r) => r.data)
export const deleteAnalysis = (id) => client.delete(`/api/analyses/${id}`)
