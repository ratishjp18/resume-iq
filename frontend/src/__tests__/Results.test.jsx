import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Results from '../pages/Results'
import * as api from '../services/api'
import { analysisFixture } from './fixtures'

vi.mock('../services/api', async () => ({ ...(await vi.importActual('../services/api')), getAnalysis: vi.fn() }))
vi.mock('../components/Charts', () => ({
  StatusDonut: () => <div data-testid="donut" />,
  CategoryBars: () => <div data-testid="bars" />,
}))

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/analysis/7']}>
      <Routes><Route path="/analysis/:id" element={<Results />} /></Routes>
    </MemoryRouter>,
  )

it('renders metrics, evidence, gaps and recommendations', async () => {
  api.getAnalysis.mockResolvedValue(analysisFixture)
  renderPage()
  expect(await screen.findByRole('heading', { name: 'Backend Engineer' })).toBeInTheDocument()
  expect(screen.getByTestId('coverage-detail')).toHaveTextContent('2 of 4')
  expect(screen.getByTestId('similarity')).toHaveTextContent('0.42')
  expect(screen.getByText(/not an official ATS score/i)).toBeInTheDocument()
  expect(screen.getByText('Built REST APIs in Python for billing.')).toBeInTheDocument()
  expect(screen.getByText('Listed only')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('tab', { name: /not evidenced/i }))
  expect(screen.getByText('Kubernetes')).toBeInTheDocument()
  expect(screen.getByText('Not evidenced in resume.')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('tab', { name: /uncertain/i }))
  expect(screen.getByText('MySQL')).toBeInTheDocument()
  expect(screen.getByText(/Consider learning Kubernetes basics/)).toBeInTheDocument()
  expect(screen.getByText(/How these scores are calculated/)).toBeInTheDocument()
})

it('renders user-controlled text as text, not HTML', async () => {
  const evil = { ...analysisFixture, matched_skills: [{ ...analysisFixture.matched_skills[0], resume_evidence: '<img src=x onerror=alert(1)> Python' }] }
  api.getAnalysis.mockResolvedValue(evil)
  const { container } = renderPage()
  expect(await screen.findByText(/<img src=x/)).toBeInTheDocument()
  expect(container.querySelector('img')).toBeNull()
})

it('handles analyses with no identified requirements', async () => {
  api.getAnalysis.mockResolvedValue({ ...analysisFixture, requirements_total: 0, requirements_matched: 0, coverage_score: 0, matched_skills: [], uncertain_skills: [], not_evidenced_skills: [] })
  renderPage()
  expect(await screen.findByText(/No requirements could be identified/)).toBeInTheDocument()
})

it('shows an error when the analysis cannot be loaded', async () => {
  api.getAnalysis.mockRejectedValue({ response: { status: 404, data: { error: { code: 'not_found', message: 'Analysis not found.' } } } })
  renderPage()
  expect(await screen.findByRole('alert')).toHaveTextContent('Analysis not found.')
})
