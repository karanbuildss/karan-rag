import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import i18n from './i18n'

vi.mock('react-leaflet', () => ({
  CircleMarker: ({ children }) => <div>{children}</div>,
  MapContainer: ({ children }) => <div data-testid="project-map">{children}</div>,
  Popup: ({ children }) => <div>{children}</div>,
  TileLayer: () => null,
  useMap: () => ({ fitBounds: vi.fn() }),
}))

vi.mock('recharts', () => ({
  Bar: () => null,
  BarChart: ({ children }) => <div>{children}</div>,
  CartesianGrid: () => null,
  Cell: () => null,
  ComposedChart: ({ children }) => <div>{children}</div>,
  Legend: () => null,
  Line: () => null,
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}))

vi.mock('./api/client', () => ({
  askInvestigator: vi.fn(),
  completeVerification: vi.fn(),
  confirmMockVerification: vi.fn(),
  createFeedback: vi.fn(),
  getDocument: vi.fn(),
  getDocumentPage: vi.fn(),
  getDocumentReviewQueue: vi.fn(),
  getDocuments: vi.fn(),
  getBudgetComparison: vi.fn(),
  getFiscalYears: vi.fn(),
  getFeedbackSummary: vi.fn(),
  getFeedback: vi.fn(),
  getCurrentAccount: vi.fn(),
  getAnomalies: vi.fn(),
  getHealth: vi.fn(),
  getLocalGovernments: vi.fn(),
  getProjectDiscoverySummary: vi.fn(),
  getProjectEvidence: vi.fn(),
  getProjectMoneyTrail: vi.fn(),
  getProjects: vi.fn(),
  getSectors: vi.fn(),
  loginAccount: vi.fn(),
  registerAccount: vi.fn(),
  reviewDocumentPage: vi.fn(),
  startMockVerification: vi.fn(),
  updateFeedback: vi.fn(),
}))

import {
  getBudgetComparison,
  getDocument,
  getDocumentPage,
  getDocuments,
  getDocumentReviewQueue,
  getFiscalYears,
  getFeedbackSummary,
  getFeedback,
  getCurrentAccount,
  getAnomalies,
  getHealth,
  getLocalGovernments,
  getProjectDiscoverySummary,
  getProjectEvidence,
  getProjectMoneyTrail,
  getProjects,
  getSectors,
  registerAccount,
  startMockVerification,
  confirmMockVerification,
  completeVerification,
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
    getCurrentAccount.mockResolvedValue({ data: { authenticated: false } })
    getFeedbackSummary.mockResolvedValue({
      data: {
        all_citizens: { count: 0, average_completion: null },
        verified_citizens: { count: 0, average_completion: null },
        verified_local_residents: { count: 0, average_completion: null },
      },
    })
    getFeedback.mockResolvedValue({ data: [] })
    getDocumentReviewQueue.mockResolvedValue({ data: [] })
    getAnomalies.mockResolvedValue({ data: [] })
    getProjects.mockResolvedValue({ data: discoveryProjects })
    getProjectDiscoverySummary.mockResolvedValue(discoverySummary)
    getLocalGovernments.mockResolvedValue({
      data: [{ code: 'PKR', name_en: 'Pokhara Metropolitan City', name_np: 'पोखरा महानगरपालिका' }],
    })
    getFiscalYears.mockResolvedValue({
      data: [
        {
          code: '2081-82',
          year_bs: '2081/82',
          year_ad: '2024/25',
          label_np: 'आर्थिक वर्ष २०८१/८२',
        },
        { code: '2078-79', year_bs: '2078/79' },
        { code: '2077-78', year_bs: '2077/78' },
      ],
    })
    getSectors.mockResolvedValue({
      data: [{ code: 'infrastructure', name_en: 'Infrastructure', name_np: 'पूर्वाधार' }],
    })
    getBudgetComparison.mockResolvedValue({
      data: {
        fiscal_year: { code: '2081-82', year_bs: '2081/82', year_ad: '2024/25' },
        currency: 'NPR',
        records: [
          {
            id: 1,
            local_government_code: 'KMC',
            local_government_name_en: 'Kathmandu Metropolitan City',
            local_government_name_np: 'काठमाडौं महानगरपालिका',
            sector_code: 'INF',
            sector_name_en: 'Infrastructure Development',
            sector_name_np: 'पूर्वाधार विकास',
            allocated_amount: '11393117282.00',
            spent_amount: '5986032901.19',
            utilization_percent: '52.54',
            review_status: 'reviewed',
            reliability: 'strong',
            comparability: 'strong',
            source_scope_en: 'Broad signed municipal sector total.',
            source_scope_np: 'हस्ताक्षरित बृहत् नगर क्षेत्रगत जम्मा।',
            data_classification: 'official',
            citation: {
              document_id: '00000000-0000-0000-0000-000000000010',
              document_title: 'Kathmandu Sectoral Budget and Expenditure 2081/82',
              page: 1,
              source_url: 'https://new.kathmandu.gov.np/official-source',
            },
          },
          {
            id: 2,
            local_government_code: 'HETAUDA',
            local_government_name_en: 'Hetauda Sub-Metropolitan City',
            local_government_name_np: 'हेटौंडा उपमहानगरपालिका',
            sector_code: 'INF',
            sector_name_en: 'Infrastructure Development',
            sector_name_np: 'पूर्वाधार विकास',
            allocated_amount: '774162667.00',
            spent_amount: '275534521.00',
            utilization_percent: '35.59',
            review_status: 'reviewed',
            reliability: 'strong',
            comparability: 'limited',
            source_scope_en: 'Narrower infrastructure programme total from progress page 23.',
            source_scope_np: 'प्रगति पृष्ठ २३ को साँघुरो पूर्वाधार कार्यक्रम जम्मा।',
            data_classification: 'official',
            citation: {
              document_id: '00000000-0000-0000-0000-000000000011',
              document_title: 'Hetauda Annual Progress Review 2081/82',
              page: 23,
              source_url: 'https://hetaudamun.gov.np/official-source',
            },
          },
        ],
        evidence_summary: {
          record_count: 2,
          municipality_count: 2,
          sector_count: 1,
          reviewed_only: true,
          note_en: 'Only reviewed values with page citations are included.',
          note_np: 'पृष्ठ उद्धरण भएका समीक्षा गरिएका मान मात्र समावेश छन्।',
        },
      },
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
      expect(screen.getByRole('status')).toHaveTextContent('Evidence services connected')
    })
  })

  it('keeps a clear browsing fallback when the API is unavailable', async () => {
    getHealth.mockRejectedValue(new Error('offline'))
    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent(
        'Evidence services unavailable · try again shortly',
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

  it('shows a project feedback shortcut only after citizen verification', async () => {
    window.history.replaceState(
      {},
      '',
      '/projects/6f3ef140-e6b9-4d6b-915f-74080c804208',
    )
    getProjectMoneyTrail.mockResolvedValue(moneyTrail)
    getCurrentAccount.mockResolvedValue({
      data: { authenticated: true, identity_verified: true },
    })
    render(<App />)

    const shortcut = await screen.findByRole('link', {
      name: 'Give verified project feedback',
    })
    expect(shortcut).toHaveAttribute('href', '#accountability')
  })

  it('distinguishes a Rupa payment date from an unpublished payment amount', async () => {
    window.history.replaceState(
      {},
      '',
      '/projects/0ad85beb-fe04-59dc-8032-aa213d0236e8',
    )
    getProjectMoneyTrail.mockResolvedValue({
      data: {
        ...moneyTrail.data,
        project: {
          ...moneyTrail.data.project,
          id: '0ad85beb-fe04-59dc-8032-aa213d0236e8',
          code: 'RUPA-W02-ANDHERI-CULVERT-2080-81',
          title_en: 'Andheri Khola Culvert Construction, Rupa-2',
          description_en:
            'Official Ward 2 project implementation row in the Rupa FY 2080/81 annual progress report.',
          status: 'implementation',
          data_classification: 'official',
          data_note_en:
            'Agreement 2080/12/28; monitoring 2081/02/02; payment date 2081/02/03. No payment amount or completion percentage is reported.',
          source_url: 'https://rupamun.gov.np/annual-progress-report',
          local_government: {
            name_en: 'Rupa Rural Municipality',
            name_np: 'रूपा गाउँपालिका',
          },
          ward_number: 2,
          fiscal_year: { year_bs: '2080/81' },
          subsector: { name_en: 'Culverts and Bridges', name_np: 'कल्भर्ट तथा पुल' },
        },
        financial_summary: {
          allocated_amount: '200000.00',
          contracted_amount: null,
          reported_paid_amount: null,
          reported_contract_balance: null,
          payment_reporting_status: 'date_reported_amount_missing',
        },
        evidence_coverage: {
          allocation: { status: 'amount_reported', amount: '200000.00' },
          agreement: { status: 'date_reported', date_bs: '2080/12/28' },
          monitoring: { status: 'date_reported', date_bs: '2081/02/02' },
          procurement: { status: 'not_found' },
          contract_award: { status: 'not_found' },
          payment: {
            status: 'date_reported_amount_missing',
            date_bs: '2081/02/03',
            amount: null,
          },
          physical_progress: {
            status: 'status_reported_percentage_missing',
            project_status: 'implementation',
            percentage: null,
          },
        },
        evidence_events: [],
        procurement: [],
        payments: [],
        milestones: [],
      },
    })
    render(<App />)

    expect(
      await screen.findByRole('heading', {
        name: 'Andheri Khola Culvert Construction, Rupa-2',
      }),
    ).toBeInTheDocument()
    expect(screen.getAllByText('In implementation').length).toBeGreaterThan(0)
    expect(
      screen.getByText(/does not publish a numeric completion percentage/i),
    ).toBeInTheDocument()
    expect(screen.getByText('Amount not published')).toBeInTheDocument()
    expect(
      screen.getByText(/official payment date is recorded, but the amount is not published/i),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', {
        name: 'What is verified—and what record is still needed',
      }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/records 2081\/02\/03 BS as the payment date/i),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Records needed to complete this money trail' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/missing contract or payment amount is not treated as zero/i),
    ).toBeInTheDocument()
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

  it('keeps the complete branded navigation on a secondary route', async () => {
    window.history.replaceState({}, '', '/compare')

    render(<App />)

    expect(
      await screen.findByRole('heading', {
        name: 'Compare reported budget and spending without hiding evidence gaps.',
      }),
    ).toBeInTheDocument()
    const header = screen.getByRole('banner')
    const navigation = within(header).getByRole('navigation', { name: 'Primary navigation' })
    const logo = within(header).getByRole('img', { name: 'Budget Darpan' })

    expect(header).toHaveClass('site-header')
    expect(logo).toHaveAttribute('src', '/logo-codefest.svg')
    for (const name of [
      'Projects',
      'Compare',
      'Map',
      'Review indicators',
      'Source library',
      'Civic investigator',
    ]) {
      expect(within(navigation).getByRole('link', { name })).toBeInTheDocument()
    }
    expect(within(header).getByRole('link', { name: 'Account' })).toBeInTheDocument()
    expect(within(header).getByRole('link', { name: 'History' })).toBeInTheDocument()
    expect(within(navigation).getByRole('link', { name: 'Compare' })).toHaveAttribute(
      'aria-current',
      'page',
    )
  })

  it('renders hosted metadata as an official source record with cited context', async () => {
    const documentId = '00000000-0000-0000-0000-000000000005'
    const projectId = '6f3ef140-e6b9-4d6b-915f-74080c804208'
    window.history.replaceState({}, '', `/documents/${documentId}?page=5`)
    getDocument.mockResolvedValue({
      data: {
        id: documentId,
        title_en: 'Pokhara Jalpa Marg Footpath Bid Addendum 2082/83',
        title_np: '',
        document_type: 'procurement_notice',
        processing_status: 'pending',
        hosted_metadata_only: true,
        file_url: null,
        source_url: 'https://bolpatra.gov.np/egp/searchOpportunity',
        source_note: 'Official procurement portal record.',
        fiscal_year_bs: '2082/83',
        local_government_name_en: 'Pokhara Metropolitan City',
        local_government_name_np: 'पोखरा महानगरपालिका',
        page_count: 5,
        pages: [],
        catalog_evidence: [
          {
            kind: 'project_evidence',
            relationship: 'procurement',
            page_from: 5,
            page_to: 5,
            section: 'Bid addendum',
            summary_en: 'The official addendum extends the cited procurement record.',
            summary_np: '',
            project: {
              id: projectId,
              code: 'PKR-JALPA-2082-83',
              title_en: 'Jalpa Marg Footpath Procurement',
              title_np: '',
            },
          },
        ],
      },
    })

    render(<App />)

    expect(await screen.findByText('Official source record')).toBeInTheDocument()
    expect(screen.getByText('Cited page 5')).toBeInTheDocument()
    expect(
      screen.getByText('The official addendum extends the cited procurement record.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Open related project/i })).toHaveAttribute(
      'href',
      `/projects/${projectId}`,
    )
    expect(screen.queryByText('This page has not been extracted or accepted yet.')).not.toBeInTheDocument()
    expect(getDocumentPage).not.toHaveBeenCalled()
  })

  it('discovers projects while keeping unknown allocations visible', async () => {
    window.history.replaceState({}, '', '/budgets')
    render(<App />)

    expect(
      await screen.findByRole('heading', {
        name: 'Explore reviewed municipal money and the projects it can support.',
      }),
    ).toBeInTheDocument()
    expect(await screen.findByText('Jalpa Marg Ward 8 Road Works')).toBeInTheDocument()
    expect(screen.getByText('Jalpa Marg Upgrading Procurement 2078/79')).toBeInTheDocument()
    expect(screen.getByText('2 project records')).toBeInTheDocument()
    expect(screen.getByText('Unknown means not evidenced, not zero.')).toBeInTheDocument()
    expect(screen.getAllByText('Unknown').length).toBeGreaterThan(0)
  })

  it('shows reviewed municipality totals instead of dead-end zero cards', async () => {
    window.history.replaceState({}, '', '/budgets?municipality=HETAUDA')
    getProjects.mockResolvedValueOnce({ data: [] })
    getProjectDiscoverySummary.mockResolvedValueOnce({
      data: {
        totals: {
          project_count: 0,
          known_allocation_count: 0,
          unknown_allocation_count: 0,
          allocated_total: null,
          evidence_project_count: 0,
          procurement_project_count: 0,
          payment_reported_project_count: 0,
          geolocated_project_count: 0,
          currency: 'NPR',
        },
        by_fiscal_year: [],
        by_sector: [],
        by_status: [],
      },
    })
    getBudgetComparison.mockResolvedValueOnce({
      data: {
        fiscal_year: { code: '2081-82', year_bs: '2081/82', year_ad: '2024/25' },
        currency: 'NPR',
        records: [
          {
            id: 8,
            local_government_code: 'HETAUDA',
            local_government_name_en: 'Hetauda Sub-Metropolitan City',
            local_government_name_np: 'हेटौंडा उपमहानगरपालिका',
            sector_code: 'INF',
            sector_name_en: 'Infrastructure Development',
            sector_name_np: 'पूर्वाधार विकास',
            allocated_amount: '774162667.00',
            spent_amount: '275534521.00',
            utilization_percent: '35.59',
            source_scope_en: 'Infrastructure programme total on PDF page 23.',
            source_scope_np: 'PDF पृष्ठ २३ को पूर्वाधार कार्यक्रम जम्मा।',
            citation: {
              document_id: '00000000-0000-0000-0000-000000000012',
              page: 23,
            },
          },
        ],
        evidence_summary: {
          record_count: 1,
          municipality_count: 1,
          sector_count: 1,
          reviewed_only: true,
          note_en: 'Only reviewed values with page citations are included.',
          note_np: 'पृष्ठ उद्धरण भएका समीक्षा गरिएका मान मात्र समावेश छन्।',
        },
      },
    })

    render(<App />)

    expect(
      await screen.findByRole('heading', {
        name: 'Official budget and reported spending are available',
      }),
    ).toBeInTheDocument()
    expect(screen.getByRole('table')).toHaveTextContent('Infrastructure Development')
    expect(screen.getByRole('table')).toHaveTextContent('35.59%')
    expect(screen.getByRole('link', { name: 'Inspect source · page 23' })).toHaveAttribute(
      'href',
      '/documents/00000000-0000-0000-0000-000000000012?page=23',
    )
    expect(screen.getByText(/will not turn these municipality totals into fake projects/i))
      .toBeInTheDocument()
    expect(screen.queryByText('Known allocation total')).not.toBeInTheDocument()
    expect(getBudgetComparison).toHaveBeenCalledWith({ municipality: 'HETAUDA' })
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

  it('renders cited municipal comparison and an honest empty-map state', async () => {
    window.history.replaceState({}, '', '/compare?fiscalYear=2081-82')
    const { unmount } = render(<App />)

    expect(
      await screen.findByRole('heading', {
        name: 'Compare reported budget and spending without hiding evidence gaps.',
      }),
    ).toBeInTheDocument()
    expect(screen.getByRole('table')).toHaveTextContent('Kathmandu Metropolitan City')
    expect(screen.getByRole('table')).toHaveTextContent('Hetauda Sub-Metropolitan City')
    expect(screen.getByText('Limited comparability')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Inspect source · page 23' })).toHaveAttribute(
      'href',
      '/documents/00000000-0000-0000-0000-000000000011?page=23',
    )
    expect(getBudgetComparison).toHaveBeenCalledWith(
      expect.objectContaining({ fiscal_year: '2081-82' }),
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

  it('shows deterministic anomaly explanations without accusation language', async () => {
    window.history.replaceState({}, '', '/anomalies')
    getAnomalies.mockResolvedValue({
      data: [{
        id: 'flag-1',
        project: '6f3ef140-e6b9-4d6b-915f-74080c804208',
        rule_id: 'LINKED_SCOPE_AMOUNT_GAP',
        severity: 'medium',
        reliability: 'limited',
        title_en: 'Linked allocation and tender estimate differ substantially',
        title_np: 'जोडिएको विनियोजन र बोलपत्र अनुमानमा ठूलो अन्तर छ',
        reason_en: 'The records may cover different scopes or packages.',
        reason_np: 'अभिलेखले फरक कार्यक्षेत्र समेट्न सक्छ।',
        data_used: { allocated_amount: '800000.00' },
        threshold: { ratio_min: '2.00' },
        calculated_values: { ratio: '11.85' },
        possible_explanations: [{
          en: 'The budget line may fund only part of a larger tender.',
          np: 'बजेट शीर्षकले ठूलो बोलपत्रको केही भाग मात्र वित्तपोषण गरेको हुन सक्छ।',
        }],
        recommendation_en: 'Verify project scope before comparison.',
        recommendation_np: 'तुलनाअघि कार्यक्षेत्र प्रमाणित गर्नुहोस्।',
        source_references: [],
      }],
    })
    render(<App />)

    expect(await screen.findByText('Linked allocation and tender estimate differ substantially')).toBeInTheDocument()
    expect(screen.getByText('{"ratio_min":"2.00"}')).toBeInTheDocument()
    expect(screen.getByText(/does not accuse/i)).toBeInTheDocument()
    expect(screen.queryByText(/fraud detected/i)).not.toBeInTheDocument()
  })

  it('completes the browser side of the mock one-time-code verification flow', async () => {
    window.history.replaceState({}, '', '/verify')
    getCurrentAccount.mockResolvedValue({ data: { authenticated: true, identity_verified: false } })
    startMockVerification.mockResolvedValue({ data: { challenge_id: 'challenge-1', demo_otp: '123456' } })
    confirmMockVerification.mockResolvedValue({ data: { code: 'one-time-code-value-1234' } })
    completeVerification.mockResolvedValue({ data: { username: 'citizen', identity_verified: true } })
    const user = userEvent.setup()
    render(<App />)

    await user.type(await screen.findByLabelText('Demo phone number'), '9800000001')
    await user.type(screen.getByLabelText('Demo citizenship number'), 'TEST-PKR-0001')
    await user.click(screen.getByRole('button', { name: 'Match demo identity' }))
    expect(await screen.findByDisplayValue('123456')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Confirm verification' }))
    expect(await screen.findByText('Mock verification completed')).toBeInTheDocument()
  })

  it('shows the precise registration validation error returned by the API', async () => {
    window.history.replaceState({}, '', '/login')
    registerAccount.mockRejectedValueOnce({
      response: {
        data: {
          errors: [{ code: 'username_taken', field: 'username', message: 'An account with this username already exists.' }],
        },
      },
    })
    const user = userEvent.setup()
    render(<App />)

    await user.click(await screen.findByRole('tab', { name: 'Create account' }))
    await user.type(screen.getByLabelText('Username'), 'existing-user')
    await user.type(screen.getByLabelText('Password'), 'safe-demo-password')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'An account with this username already exists.',
    )
  })

  it('protects the document review screen from public accounts', async () => {
    window.history.replaceState({}, '', '/admin-documents')
    getCurrentAccount.mockResolvedValue({ data: { authenticated: false } })
    render(<App />)

    expect(await screen.findByText(/authorized demo operator account/i)).toHaveAttribute(
      'href',
      '/login?returnTo=%2Fadmin-documents',
    )
    expect(getDocumentReviewQueue).not.toHaveBeenCalled()
  })
})
