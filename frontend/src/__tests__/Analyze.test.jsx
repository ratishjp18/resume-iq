import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Analyze from '../pages/Analyze'
import * as api from '../services/api'

vi.mock('../services/api', async () => {
  const actual = await vi.importActual('../services/api')
  return { ...actual, uploadResume: vi.fn(), createJob: vi.fn(), createAnalysis: vi.fn(), deleteResume: vi.fn(() => Promise.resolve()) }
})

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/analyze']}>
      <Routes>
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/analysis/:id" element={<div>RESULTS PAGE</div>} />
      </Routes>
    </MemoryRouter>,
  )

const pdf = (name = 'resume.pdf', size = 2048) => new File([new Uint8Array(size)], name, { type: 'application/pdf' })
const RESUME = { id: 3, original_filename: 'resume.pdf', file_type: 'pdf', extracted_text: 'Alex Sample - Python developer', word_count: 5, char_count: 30 }
const JD = 'We need a backend engineer with strong Python and Docker experience.'

async function uploadValid() {
  api.uploadResume.mockResolvedValue(RESUME)
  await userEvent.upload(screen.getByTestId('file-input'), pdf())
  await screen.findByTestId('resume-preview')
}
async function fillJob() {
  await userEvent.type(screen.getByLabelText(/job title/i), 'Engineer')
  await userEvent.type(screen.getByLabelText(/job description/i), JD)
}
const clickAnalyze = () => userEvent.click(screen.getByRole('button', { name: /^analyze$/i }))

beforeEach(() => vi.clearAllMocks())

it('rejects unsupported file types client-side without calling the API', async () => {
  renderPage()
  await userEvent.upload(screen.getByTestId('file-input'), new File(['x'], 'notes.txt', { type: 'text/plain' }), { applyAccept: false })
  expect(await screen.findByRole('alert')).toHaveTextContent(/Unsupported file type/)
  expect(api.uploadResume).not.toHaveBeenCalled()
})

it('rejects oversized files', async () => {
  renderPage()
  await userEvent.upload(screen.getByTestId('file-input'), pdf('big.pdf', 5 * 1024 * 1024 + 1))
  expect(await screen.findByRole('alert')).toHaveTextContent(/too large/)
})

it('uploads a valid file, shows size and extracted text preview', async () => {
  renderPage()
  await uploadValid()
  expect(screen.getByTestId('resume-preview')).toHaveTextContent('5 words')
  expect(screen.getByTestId('file-size')).toHaveTextContent('2.0 KB')
  await userEvent.click(screen.getByRole('button', { name: /preview text/i }))
  expect(screen.getByText('Alex Sample - Python developer')).toBeInTheDocument()
})

it('shows backend upload errors', async () => {
  api.uploadResume.mockRejectedValue({ response: { status: 422, data: { error: { code: 'no_extractable_text', message: 'No readable text was found. Scanned documents need OCR.' } } } })
  renderPage()
  await userEvent.upload(screen.getByTestId('file-input'), pdf())
  expect(await screen.findByRole('alert')).toHaveTextContent(/Scanned documents need OCR/)
})

it('validates job fields before submitting', async () => {
  renderPage()
  await uploadValid()
  await clickAnalyze()
  expect(await screen.findByText(/Enter a job title/)).toBeInTheDocument()
  expect(screen.getByText(/Paste the job description/)).toBeInTheDocument()
  expect(api.createJob).not.toHaveBeenCalled()
})

it('requires a resume before analysis', async () => {
  renderPage()
  await fillJob()
  await clickAnalyze()
  expect(await screen.findByRole('alert')).toHaveTextContent(/Upload a resume first/)
})

it('shows a processing state and navigates to results on success', async () => {
  api.createJob.mockResolvedValue({ id: 4 })
  let resolve
  api.createAnalysis.mockReturnValue(new Promise((r) => { resolve = r }))
  renderPage()
  await uploadValid()
  await fillJob()
  await clickAnalyze()
  expect(await screen.findByTestId('processing')).toBeInTheDocument()
  expect(api.createAnalysis).toHaveBeenCalledWith(3, 4)
  resolve({ id: 9 })
  expect(await screen.findByText('RESULTS PAGE')).toBeInTheDocument()
})

it('shows an API error and leaves the loading state when analysis fails', async () => {
  api.createJob.mockResolvedValue({ id: 4 })
  api.createAnalysis.mockRejectedValue(new Error('network'))
  renderPage()
  await uploadValid()
  await fillJob()
  await clickAnalyze()
  expect(await screen.findByRole('alert')).toHaveTextContent(/Cannot reach the ResumeIQ backend/)
  await waitFor(() => expect(screen.queryByTestId('processing')).not.toBeInTheDocument())
})
