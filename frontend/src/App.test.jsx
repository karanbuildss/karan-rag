import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import i18n from './i18n'

vi.mock('react-leaflet', () => ({
  CircleMarker: ({ children }) => <div>{children}</div>,
  MapContainer: ({ children }) => <div data-testid="project-map">{children}</div>,
  Popup: ({ children }) => <div>{children}</div>,
  TileLayer: () => null,
}))

vi.mock('recharts', () => ({
  Bar: () => null,
  BarChart: ({ children }) => <div>{children}</div>,
  CartesianGrid: () => null,
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}))

vi.mock('./api/client', () => ({
  askInvestigator: vi.fn(),
  getDocument: vi.fn(),
  getDocumentPage: vi.fn(),
  getDocuments: vi.fn(),
  getFiscalYears: vi.fn(),
  getHealth: vi.fn(),
  getLocalGovernments: vi.fn(),
  getProjectDiscoverySummary: vi.fn(),
  getProjectEvidence: vi.fn(),
  getProjectMoneyTrail: vi.fn(),
  getProjects: vi.fn(),
  getSectors: vi.fn(),
}))

import {
  getDocuments,
  getFiscalYears,
  getHealth,
  getLocalGovernments,
  getProjectDiscoverySummary,
  getProjectEvidence,
  getProjectMoneyTrail,
  getProjects,
  getSectors,
} from './api/client'

const moneyTrail = {
  data: {
    project: {
      id: '6f3ef140-e6b9-4d6b-915f-74080c804208',
      code: 'PKR-W08-JALPA-2077-78',
      title_en: 'Jalpa Marg Ward 8 Road Works',
      title_np: 'जाल्पा मार्ग वडा नं. ८ सडक कार्य',
      description_en: 'Evidence-backed project reconstruction.',
      description_np: 'प्रमाणमा आधारित आयोजना पुनर्निर्माण।',
      status: 'unknown',
      official_progress_percent: null,
      planned_end_date: null,
      data_classification: 'reconstructed_from_official_sources',
      data_note_en:
        'The tender estimate is not a contract value. Award, payments, progress, and coordinates remain unknown.',
      data_note_np: 'बोलपत्र, भुक्तानी, प्रगति र स्थानको प्रमाण अझै उपलब्ध छैन।',
      local_government: {
        name_en: 'Pokhara Metropolitan City',
        name_np: 'पोखरा महानगरपालिका',
      },
      ward_number: 8,
      fiscal_year: { year_bs: '2077/78' },
      subsector: { name_en: 'Roads', name_np: 'सडक' },
      location: null,
    },
    financial_summary: {
      allocated_amount: '800000.00',
      contracted_amount: null,
      reported_paid_amount: null,
      reported_contract_balance: null,
      payment_reporting_status: 'not_yet_reported',
    },
    procurement: [
      {
        reference: '45/PMC/NCB/W/077-78',
        invitation_number: '16.1/PMC/077-78',
        title_en: 'Upgrading of Jalpa Marga Road, PMC-08',
        title_np: 'जाल्पा मार्ग सडक स्तरोन्नति, पोखरा-८',
        procurement_method: 'open_competitive',
        published_date: '2021-01-28',
        bid_submission_deadline: '2021-02-28T12:00:00+05:45',
        estimated_amount: '9477987.16',
        bid_security_amount: '270000.00',
        data_note_en:
          'Official tender estimate excluding VAT and contingencies. It is not an awarded contract or payment amount.',
        data_note_np: 'यो प्रदान गरिएको ठेक्का वा भुक्तानी रकम होइन।',
        source_url: 'https://bolpatra.gov.np/egp/searchOpportunity',
        data_classification: 'official',
        award: null,
      },
    ],
    payments: [],
    milestones: [],
  },
}

const discoveryProjects = [
  {
    id: '6f3ef140-e6b9-4d6b-915f-74080c804208',
    code: 'PKR-W08-JALPA-2077-78',
    title_en: 'Jalpa Marg Ward 8 Road Works',
    title_np: 'जाल्पा मार्ग वडा नं. ८ सडक कार्य',
    status: 'unknown',
    allocated_amount: '800000.00',
    data_note_en: 'Award, payment, progress, and coordinates remain unknown.',
    data_note_np: 'ठेक्का, भुक्तानी, प्रगति र निर्देशाङ्क अज्ञात छन्।',
    local_government_name_en: 'Pokhara Metropolitan City',
    local_government_name_np: 'पोखरा महानगरपालिका',
    ward_number: 8,
    fiscal_year_code: '2077-78',
    subsector_name_en: 'Roads',
    subsector_name_np: 'सडक',
    evidence_count: 4,
    tender_count: 1,
    location: null,
  },
  {
    id: '2fb7eb1c-8b5a-4df8-9737-5c2dbb5399c4',
    code: 'PKR-W08-JALPA-UPGRADE-2078-79',
    title_en: 'Jalpa Marg Upgrading Procurement 2078/79',
    title_np: 'जाल्पा मार्ग स्तरोन्नति खरिद २०७८/७९',
    status: 'unknown',
    allocated_amount: null,
    data_note_en: 'Only the procurement notice is available.',
    data_note_np: 'खरिद सूचना मात्र उपलब्ध छ।',
    local_government_name_en: 'Pokhara Metropolitan City',
    local_government_name_np: 'पोखरा महानगरपालिका',
    ward_number: 8,
    fiscal_year_code: '2078-79',
    subsector_name_en: 'Roads',
    subsector_name_np: 'सडक',
    evidence_count: 1,
    tender_count: 1,
    location: null,
  },
]

const discoverySummary = {
  data: {
    totals: {
      project_count: 2,
      known_allocation_count: 1,
      unknown_allocation_count: 1,
      allocated_total: '800000.00',
      evidence_project_count: 2,
      procurement_project_count: 2,
      payment_reported_project_count: 0,
      geolocated_project_count: 0,
      currency: 'NPR',
    },
    by_fiscal_year: [],
    by_sector: [],
    by_status: [{ status: 'unknown', project_count: 2 }],
  },
}

describe('Budget Darpan foundation', () => {
  beforeEach(async () => {
    window.history.replaceState({}, '', '/')
    await i18n.changeLanguage('en')
    document.documentElement.lang = 'en'
    getProjectEvidence.mockResolvedValue({ data: [] })
    getProjects.mockResolvedValue({ data: discoveryProjects })
    getProjectDiscoverySummary.mockResolvedValue(discoverySummary)
    getLocalGovernments.mockResolvedValue({
      data: [{ code: 'PKR', name_en: 'Pokhara Metropolitan City', name_np: 'पोखरा महानगरपालिका' }],
    })
    getFiscalYears.mockResolvedValue({
      data: [
        { code: '2078-79', year_bs: '2078/79' },
        { code: '2077-78', year_bs: '2077/78' },
      ],
    })
    getSectors.mockResolvedValue({
      data: [{ code: 'infrastructure', name_en: 'Infrastructure', name_np: 'पूर्वाधार' }],
    })
  })

  afterEach(() => {
    cleanup()
    vi.clearAllMocks()
  })

  it('switches the complete interface from English to Nepali', async () => {
    getHealth.mockResolvedValue({ data: { status: 'ok' } })
    const user = userEvent.setup()
    render(<App />)

    expect(
      screen.getByRole('heading', {
        name: 'See where public money goes—and the evidence behind it.',
      }),
    ).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /नेपाली/i }))

    expect(
      screen.getByRole('heading', {
        name: 'सार्वजनिक पैसा कहाँ जान्छ—र त्यसको प्रमाण हेर्नुहोस्।',
      }),
    ).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('np')
  })

  it('shows backend health when the API is reachable', async () => {
    getHealth.mockResolvedValue({ data: { status: 'ok' } })
    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent('Local API connected')
    })
  })

  it('keeps a clear browsing fallback when the API is unavailable', async () => {
    getHealth.mockRejectedValue(new Error('offline'))
    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent(
        'API unavailable · browsing fallback remains',
      )
    })
  })

  it('renders the real evidence-backed project with unknown fields kept explicit', async () => {
    window.history.replaceState(
      {},
      '',
      '/projects/6f3ef140-e6b9-4d6b-915f-74080c804208',
    )
    getProjectMoneyTrail.mockResolvedValue(moneyTrail)
    getProjectEvidence.mockResolvedValue({
      data: [
        {
          relationship: 'audit',
          page_from: 48,
          evidence_note_en:
            'The audit names the Ward 8 Jalpa Marg work and P.L. Construction.',
          evidence_note_np: 'लेखापरीक्षणमा वडा नं. ८ जाल्पा मार्ग र पि.एल. कन्स्ट्रक्सन उल्लेख छ।',
          document: {
            id: '00000000-0000-0000-0000-000000000002',
            title_en: 'Pokhara Metropolitan City Audit Report 2077/78',
            title_np: 'पोखरा महानगरपालिका लेखापरीक्षण प्रतिवेदन २०७७/७८',
            source_url: 'https://oag.gov.np/reports/local-level-report',
          },
        },
        {
          relationship: 'procurement',
          page_from: 1,
          evidence_note_en:
            'The official FY 2077/78 tender identifies the road name, ward, IFB, and estimate.',
          evidence_note_np: 'आधिकारिक बोलपत्रले सडक, वडा, IFB र अनुमान पहिचान गर्छ।',
          document: {
            id: '00000000-0000-0000-0000-000000000003',
            title_en: 'Pokhara Jalpa Marg Upgrading Bidding Document 2077/78',
            title_np: 'पोखरा जाल्पा मार्ग स्तरोन्नति बोलपत्र कागजात २०७७/७८',
            source_url: 'https://bolpatra.gov.np/egp/searchOpportunity',
          },
        },
      ],
    })
    render(<App />)

    expect(
      await screen.findByRole('heading', {
        name: 'Jalpa Marg Ward 8 Road Works',
      }),
    ).toBeInTheDocument()
    expect(screen.getByText('Reconstructed from official sources')).toBeInTheDocument()
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    expect(
      await screen.findByText('No coordinates have been reported for this project.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('No official milestone or physical-progress record has been found yet.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Procurement notice published')).toBeInTheDocument()
    expect(screen.getByText('45/PMC/NCB/W/077-78')).toBeInTheDocument()
    expect(screen.getByText(/not an awarded contract or payment amount/i)).toBeInTheDocument()
    expect(screen.getByText('No contract award has been found for this project.')).toBeInTheDocument()
    expect(
      await screen.findByText((content) => content.startsWith('Project allocation:')),
    ).toBeInTheDocument()
    expect(await screen.findByText('Official audit finding')).toBeInTheDocument()
    expect(await screen.findByText('Procurement')).toBeInTheDocument()
    expect(screen.getByText(/P\.L\. Construction/)).toBeInTheDocument()
    expect(screen.queryByText(/synthetic demo figures/i)).not.toBeInTheDocument()
  })

  it('does not turn an unknown procurement-only allocation into zero', async () => {
    window.history.replaceState(
      {},
      '',
      '/projects/2fb7eb1c-8b5a-4df8-9737-5c2dbb5399c4',
    )
    getProjectMoneyTrail.mockResolvedValue({
      data: {
        ...moneyTrail.data,
        project: {
          ...moneyTrail.data.project,
          id: '2fb7eb1c-8b5a-4df8-9737-5c2dbb5399c4',
          code: 'PKR-W08-JALPA-UPGRADE-2078-79',
          title_en: 'Jalpa Marg Upgrading Procurement 2078/79',
          fiscal_year: { year_bs: '2078/79' },
        },
        financial_summary: {
          allocated_amount: null,
          contracted_amount: null,
          reported_paid_amount: null,
          reported_contract_balance: null,
          payment_reporting_status: 'not_yet_reported',
        },
      },
    })
    render(<App />)

    expect(
      await screen.findByRole('heading', {
        name: 'Jalpa Marg Upgrading Procurement 2078/79',
      }),
    ).toBeInTheDocument()
    expect(
      screen.getByText('No comparable allocation, contract, or payment values have been reported.'),
    ).toBeInTheDocument()
  })

  it('renders registered documents with an honest source-link warning', async () => {
    window.history.replaceState({}, '', '/documents')
    getDocuments.mockResolvedValue({
      data: [
        {
          id: '00000000-0000-0000-0000-000000000001',
          title_en: 'Pokhara Annual Development Program 2082/83',
          title_np: 'पोखरा वार्षिक विकास कार्यक्रम २०८२/८३',
          document_type: 'annual_program',
          processing_status: 'needs_review',
          source_url_kind: 'landing_page',
          source_url: 'https://pokharamun.gov.np/budget-program',
          local_government_name_en: 'Pokhara Metropolitan City',
          local_government_name_np: 'पोखरा महानगरपालिका',
          fiscal_year_bs: '2082/83',
          page_count: 280,
        },
      ],
    })

    render(<App />)

    expect(
      await screen.findByRole('heading', {
        name: 'Pokhara Annual Development Program 2082/83',
      }),
    ).toBeInTheDocument()
    expect(screen.getByText(/exact attachment URL still requires verification/i)).toBeInTheDocument()
  })

  it('discovers projects while keeping unknown allocations visible', async () => {
    window.history.replaceState({}, '', '/budgets')
    render(<App />)

    expect(
      await screen.findByRole('heading', {
        name: 'Find the public project behind the budget line.',
      }),
    ).toBeInTheDocument()
    expect(await screen.findByText('Jalpa Marg Ward 8 Road Works')).toBeInTheDocument()
    expect(screen.getByText('Jalpa Marg Upgrading Procurement 2078/79')).toBeInTheDocument()
    expect(screen.getByText('2 project records')).toBeInTheDocument()
    expect(screen.getByText('Unknown means not evidenced, not zero.')).toBeInTheDocument()
    expect(screen.getAllByText('Unknown').length).toBeGreaterThan(0)
  })

  it('applies a shareable project search to list and summary requests', async () => {
    window.history.replaceState({}, '', '/budgets')
    const user = userEvent.setup()
    render(<App />)

    const search = await screen.findByRole('searchbox', { name: 'Project or reference' })
    await user.type(search, '45/PMC/NCB/W/077-78')
    await user.click(screen.getByRole('button', { name: 'Search' }))

    await waitFor(() => {
      expect(getProjects).toHaveBeenCalledWith(
        expect.objectContaining({ search: '45/PMC/NCB/W/077-78' }),
      )
      expect(getProjectDiscoverySummary).toHaveBeenCalledWith(
        expect.objectContaining({ search: '45/PMC/NCB/W/077-78' }),
      )
    })
    expect(window.location.search).toContain('search=45%2FPMC%2FNCB%2FW%2F077-78')
  })

  it('renders comparison and honest empty-map states from the same filters', async () => {
    window.history.replaceState({}, '', '/compare?fiscalYear=2077-78')
    const { unmount } = render(<App />)

    expect(await screen.findByText('Known project allocations')).toBeInTheDocument()
    expect(screen.getByRole('table')).toHaveTextContent('Jalpa Marg Ward 8 Road Works')
    expect(getProjects).toHaveBeenCalledWith(
      expect.objectContaining({ fiscal_year__code: '2077-78' }),
    )

    unmount()
    window.history.replaceState({}, '', '/map')
    render(<App />)
    expect(
      await screen.findByRole('heading', {
        name: 'No verified coordinates are available for these projects yet.',
      }),
    ).toBeInTheDocument()
    expect(screen.queryByTestId('project-map')).not.toBeInTheDocument()
  })
})
