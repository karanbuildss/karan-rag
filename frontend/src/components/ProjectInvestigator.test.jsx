import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import i18n from '../i18n'
import ProjectInvestigator from './ProjectInvestigator'

vi.mock('../api/client', () => ({
  askInvestigator: vi.fn(),
}))

import { askInvestigator } from '../api/client'

const projectId = '6f3ef140-e6b9-4d6b-915f-74080c804208'

describe('ProjectInvestigator', () => {
  afterEach(() => cleanup())

  beforeEach(async () => {
    vi.clearAllMocks()
    await i18n.changeLanguage('en')
  })

  it('submits a Romanized Nepali question and renders citations and limitations', async () => {
    askInvestigator.mockResolvedValue({
      data: {
        route: 'PROJECT_INVESTIGATION',
        language: 'romanized_ne',
        answer:
          'Allocation NPR 800,000.00 cha. Tender estimate award wa payment amount hoina.',
        citations: [
          {
            document_id: 'doc-1',
            document_title: 'Pokhara Budget Book 2077/78',
            page: 168,
            section: 'Jalpa Marg road construction',
            relationship: 'allocation',
            source_kind: 'reviewed_document_page',
            excerpt: 'Accepted text from the official budget PDF.',
            viewer_path: '/documents/doc-1?page=168',
          },
        ],
        limitations: [
          {
            code: 'payments_not_reported',
            message: 'No verified payment records are available.',
          },
        ],
        provenance: {
          document_retrieval: 'database_evidence',
          answer_generation: 'deterministic',
        },
      },
    })
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <ProjectInvestigator projectId={projectId} />
      </MemoryRouter>,
    )

    const question = 'Pokhara Ward 8 ko road project ko paisa kaha gayo?'
    await user.type(screen.getByLabelText('Your question'), question)
    await user.click(screen.getByRole('button', { name: 'Investigate the evidence' }))

    expect(askInvestigator).toHaveBeenCalledWith({ question, projectId })
    expect(await screen.findByText(/Allocation NPR 800,000.00/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Pokhara Budget Book 2077\/78/ })).toHaveAttribute(
      'href',
      '/documents/doc-1?page=168',
    )
    expect(screen.getByText('No verified payment records are available.')).toBeInTheDocument()
    expect(screen.getByText('Accepted PDF text')).toBeInTheDocument()
    expect(screen.getByText('Accepted text from the official budget PDF.')).toBeInTheDocument()
  })

  it('keeps the evidence pages available when the API is offline', async () => {
    askInvestigator.mockRejectedValue(new Error('offline'))
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <ProjectInvestigator projectId={projectId} />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('Your question'), 'How much was paid?')
    await user.click(screen.getByRole('button', { name: 'Investigate the evidence' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The investigator is temporarily unavailable',
    )
  })
})
