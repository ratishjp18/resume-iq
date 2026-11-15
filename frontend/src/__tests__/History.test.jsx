import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import History from '../pages/History'
import * as api from '../services/api'
import { historyFixture } from './fixtures'

vi.mock('../services/api', async () => ({
  ...(await vi.importActual('../services/api')),
  listAnalyses: vi.fn(), deleteAnalysis: vi.fn(), deleteResume: vi.fn(),
}))

const renderPage = () => render(<MemoryRouter><History /></MemoryRouter>)
beforeEach(() => { vi.clearAllMocks(); api.listAnalyses.mockResolvedValue(historyFixture) })

const openDeleteAnalysis = () => userEvent.click(screen.getByRole('button', { name: /delete analysis for backend engineer/i }))

it('lists previous analyses with job, company and coverage', async () => {
  renderPage()
  const items = await screen.findAllByTestId('history-item')
  expect(items).toHaveLength(2)
  expect(items[0]).toHaveTextContent('Backend Engineer')
  expect(items[0]).toHaveTextContent('Acme Corp')
  expect(items[0]).toHaveTextContent('50%')
  expect(items[1]).toHaveTextContent('No company')
  expect(within(items[0]).getByRole('link', { name: /view/i })).toHaveAttribute('href', '/analysis/7')
})

it('shows an empty state', async () => {
  api.listAnalyses.mockResolvedValue({ items: [], total: 0 })
  renderPage()
  expect(await screen.findByText('No analyses yet.')).toBeInTheDocument()
})

it('passes search and sort to the API', async () => {
  renderPage()
  await screen.findAllByTestId('history-item')
  await userEvent.type(screen.getByLabelText('Search analyses'), 'data')
  await waitFor(() => expect(api.listAnalyses).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'data' })))
  await userEvent.selectOptions(screen.getByLabelText('Sort analyses'), 'coverage:desc')
  await waitFor(() => expect(api.listAnalyses).toHaveBeenLastCalledWith(expect.objectContaining({ sort_by: 'coverage', order: 'desc' })))
})

it('asks for confirmation before deleting and does nothing on cancel', async () => {
  renderPage()
  await screen.findAllByTestId('history-item')
  await openDeleteAnalysis()
  const dialog = screen.getByRole('dialog')
  expect(dialog).toHaveTextContent(/permanently deletes the analysis/i)
  await userEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }))
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(api.deleteAnalysis).not.toHaveBeenCalled()
})

it('deletes an analysis after confirming and refreshes the list', async () => {
  api.deleteAnalysis.mockResolvedValue({})
  renderPage()
  await screen.findAllByTestId('history-item')
  await openDeleteAnalysis()
  api.listAnalyses.mockResolvedValue({ items: [historyFixture.items[1]], total: 1 })
  await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete analysis' }))
  await waitFor(() => expect(api.deleteAnalysis).toHaveBeenCalledWith(7))
  await waitFor(() => expect(screen.getAllByTestId('history-item')).toHaveLength(1))
})

it('deletes saved resume data after confirming', async () => {
  api.deleteResume.mockResolvedValue({})
  renderPage()
  await screen.findAllByTestId('history-item')
  await userEvent.click(screen.getByRole('button', { name: /delete saved resume data for backend engineer/i }))
  expect(screen.getByRole('dialog')).toHaveTextContent(/every analysis created from it/)
  await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete resume data' }))
  await waitFor(() => expect(api.deleteResume).toHaveBeenCalledWith(3))
})

it('shows an error when delete fails', async () => {
  api.deleteAnalysis.mockRejectedValue({ response: { status: 404, data: { error: { message: 'Analysis not found.' } } } })
  renderPage()
  await screen.findAllByTestId('history-item')
  await openDeleteAnalysis()
  await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete analysis' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Analysis not found.')
})
