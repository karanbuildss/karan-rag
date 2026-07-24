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
        visualizations: [
          {
            id: 'financial_flow',
            type: 'bar',
            title_en: 'Allocation, contract, and reported payments',
            title_np: 'विनियोजन, ठेक्का र प्रतिवेदित भुक्तानी',
            unit: 'NPR',
            data: [
              { key: 'allocated', label_en: 'Allocated', label_np: 'विनियोजित', value: 800000 },
              { key: 'contracted', label_en: 'Contracted', label_np: 'ठेक्का रकम', value: null },
            ],
            boundary_en: 'Unknown values are omitted, never converted to zero.',
            boundary_np: 'अज्ञात मानलाई शून्यमा परिवर्तन नगरी छोडिएको छ।',
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

    expect(askInvestigator).toHaveBeenCalledWith({ question, projectId, sessionId: null })
    expect(await screen.findByText(/Allocation NPR 800,000.00/)).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Allocation, contract, and reported payments' }),
    ).toBeInTheDocument()
    expect(screen.getByText(/Allocated:.*800,000/)).toBeInTheDocument()
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

  it('keeps text input available when browser voice recognition is unsupported', () => {
    render(
      <MemoryRouter>
        <ProjectInvestigator projectId={projectId} />
      </MemoryRouter>,
    )

    expect(screen.getByText(/Voice input is not supported/)).toBeInTheDocument()
    expect(screen.getByLabelText('Your question')).toBeEnabled()
  })

  it('renders Rupa payment-date evidence without turning the missing amount into zero', async () => {
    askInvestigator.mockResolvedValue({
      data: {
        route: 'DATABASE_QUERY',
        language: 'en',
        answer:
          'The official record reports payment date 2081/02/03 BS, but the paid amount is not published; unknown does not mean zero.',
        citations: [
          {
            document_id: 'rupa-progress',
            document_title: 'Rupa Rural Municipality Annual Progress Report 2080/81',
            page: 51,
            section: 'Ward 2 project implementation status',
            relationship: 'progress',
            source_kind: 'reviewed_document_page',
            excerpt: 'Payment date 2081/02/03; no project-level paid amount is stated.',
            viewer_path: '/documents/rupa-progress?page=51',
          },
        ],
        limitations: [
          {
            code: 'payment_amount_unpublished',
            message:
              'An official payment date is recorded, but no verified paid amount is available; the amount remains unknown, not zero.',
          },
        ],
        provenance: {
          document_retrieval: 'chroma',
          answer_generation: 'ollama:qwen2.5:3b',
        },
      },
    })
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <ProjectInvestigator projectId="0ad85beb-fe04-59dc-8032-aa213d0236e8" />
      </MemoryRouter>,
    )

    const question = 'When was payment recorded, and how much was paid?'
    await user.type(screen.getByLabelText('Your question'), question)
    await user.click(screen.getByRole('button', { name: 'Investigate the evidence' }))

    expect(await screen.findByText(/payment date 2081\/02\/03 BS/)).toBeInTheDocument()
    expect(screen.getAllByText(/unknown does not mean zero|unknown, not zero/)).toHaveLength(2)
    expect(
      screen.getByRole('link', {
        name: /Rupa Rural Municipality Annual Progress Report 2080\/81/,
      }),
    ).toHaveAttribute('href', '/documents/rupa-progress?page=51')
  })
})
