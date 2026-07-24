import { useEffect, useMemo, useState } from 'react'

import {
  getBudgetComparison,
  getFiscalYears,
  getLocalGovernments,
  getProjectDiscoverySummary,
  getProjects,
  getSectors,
} from '../api/client'

const FILTER_MAP = {
  search: 'search',
  municipality: 'local_government__code',
  ward: 'ward__number',
  fiscalYear: 'fiscal_year__code',
  sector: 'subsector__sector__code',
  status: 'status',
}
export function readDiscoveryFilters(searchParams) {
  return Object.fromEntries(
    Object.keys(FILTER_MAP).map((key) => [key, searchParams.get(key) || '']),
  )
}

function buildApiParams(filters) {
  const params = {
    ordering: '-fiscal_year__code,title_en',
    page_size: 100,
  }
  Object.entries(FILTER_MAP).forEach(([key, apiKey]) => {
    if (filters[key]) params[apiKey] = filters[key]
  })
  return params
}

export default function useProjectDiscovery(searchParams) {
  const serializedFilters = searchParams.toString()
  const filters = useMemo(
    () => readDiscoveryFilters(new URLSearchParams(serializedFilters)),
    [serializedFilters],
  )
  const apiParams = useMemo(() => buildApiParams(filters), [filters])
  const budgetEvidenceParams = useMemo(() => {
    if (!filters.municipality || filters.search || filters.ward || filters.status) return null
    return {
      municipality: filters.municipality,
      ...(filters.fiscalYear ? { fiscal_year: filters.fiscalYear } : {}),
      ...(filters.sector ? { sector: filters.sector } : {}),
    }
  }, [filters])
  const [budgetEvidence, setBudgetEvidence] = useState(null)
  const [projects, setProjects] = useState([])
  const [summary, setSummary] = useState(null)
  const [options, setOptions] = useState({
    fiscalYears: [],
    localGovernments: [],
    sectors: [],
  })
  const [state, setState] = useState('loading')
  const [retryKey, setRetryKey] = useState(0)

  useEffect(() => {
    let active = true
    Promise.all([
      getLocalGovernments({ ordering: 'name_en', page_size: 100 }),
      getFiscalYears({ ordering: '-code', page_size: 100 }),
      getSectors({ ordering: 'name_en', page_size: 100 }),
    ])
      .then(([localGovernments, fiscalYears, sectors]) => {
        if (!active) return
        setOptions({
          localGovernments: localGovernments.data || [],
          fiscalYears: fiscalYears.data || [],
          sectors: sectors.data || [],
        })
      })
      .catch(() => {
        if (active) {
          setOptions({ fiscalYears: [], localGovernments: [], sectors: [] })
        }
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    setState('loading')
    Promise.all([
      getProjects(apiParams),
      getProjectDiscoverySummary(apiParams),
      budgetEvidenceParams
        ? getBudgetComparison(budgetEvidenceParams).catch(() => ({ data: null }))
        : Promise.resolve({ data: null }),
    ])
      .then(([projectResponse, summaryResponse, budgetEvidenceResponse]) => {
        if (!active) return
        setProjects(projectResponse.data || [])
        setSummary(summaryResponse.data || null)
        setBudgetEvidence(budgetEvidenceResponse.data || null)
        setState('ready')
      })
      .catch(() => {
        if (active) setState('error')
      })

    return () => {
      active = false
    }
  }, [apiParams, budgetEvidenceParams, retryKey])

  return {
    budgetEvidence,
    filters,
    options,
    projects,
    retry: () => setRetryKey((key) => key + 1),
    state,
    summary,
  }
}
