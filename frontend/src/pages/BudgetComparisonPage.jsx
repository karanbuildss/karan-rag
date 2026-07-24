import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import { getBudgetComparison, getFiscalYears } from '../api/client'
import MunicipalBudgetComparisonChart from '../components/MunicipalBudgetComparisonChart'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

const formatNpr = (value) =>
  value === null || value === undefined
    ? '—'
    : `NPR ${Number(value).toLocaleString('en-NP', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`

export default function BudgetComparisonPage() {
  const { i18n, t } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()
  const [fiscalYears, setFiscalYears] = useState([])
  const [comparison, setComparison] = useState(null)
  const [state, setState] = useState('loading')
  const isNepali = i18n.resolvedLanguage === 'np'
  const fiscalYear = searchParams.get('fiscalYear') || '2081-82'

  useEffect(() => {
    let active = true
    getFiscalYears({ ordering: '-code' })
      .then((response) => {
        if (active) setFiscalYears(response.data || [])
      })
      .catch(() => {
        if (active) setFiscalYears([])
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    setState('loading')
    getBudgetComparison({ fiscal_year: fiscalYear })
      .then((response) => {
        if (active) {
          setComparison(response.data)
          setState('ready')
        }
      })
      .catch(() => active && setState('error'))
    return () => {
      active = false
    }
  }, [fiscalYear])

  const records = comparison?.records || []
  const municipalityCount = comparison?.evidence_summary?.municipality_count || 0
  const sectorCount = comparison?.evidence_summary?.sector_count || 0
  const evidenceNote = isNepali
    ? comparison?.evidence_summary?.note_np
    : comparison?.evidence_summary?.note_en
  const changeFiscalYear = (event) => {
    const next = new URLSearchParams(searchParams)
    next.set('fiscalYear', event.target.value)
    setSearchParams(next)
  }

  return (
    <div className="flex min-h-screen flex-col bg-canvas text-ink">
      <SiteHeader compact />
      <main className="flex-1">
        <section className="border-b border-line bg-surface">
          <div className="page-shell py-10">
            <Link className="back-link" to="/budgets">← {t('municipalComparison.back')}</Link>
            <p className="eyebrow mt-8">{t('municipalComparison.eyebrow')}</p>
            <div className="mt-3 grid gap-6 lg:grid-cols-[1fr_auto] lg:items-end">
              <div>
                <h1 className="max-w-4xl font-display text-4xl font-bold text-forest">
                  {t('municipalComparison.title')}
                </h1>
                <p className="mt-4 max-w-3xl leading-7 text-muted">
                  {t('municipalComparison.description')}
                </p>
              </div>
              <label className="filter-field min-w-56">
                <span>{t('municipalComparison.fiscalYear')}</span>
                <select onChange={changeFiscalYear} value={fiscalYear}>
                  {fiscalYears.map((year) => (
                    <option key={year.code} value={year.code}>
                      {isNepali ? year.label_np : `${year.year_bs} (${year.year_ad})`}
                    </option>
                  ))}
                  {!fiscalYears.some((year) => year.code === fiscalYear) && (
                    <option value={fiscalYear}>{fiscalYear}</option>
                  )}
                </select>
              </label>
            </div>
          </div>
        </section>

        <section className="page-shell py-10">
          {state === 'loading' && <p role="status">{t('municipalComparison.loading')}</p>}
          {state === 'error' && <p role="alert">{t('municipalComparison.error')}</p>}
          {state === 'ready' && records.length === 0 && (
            <div className="discovery-state">
              <h2 className="font-display text-2xl font-bold text-forest">
                {t('municipalComparison.emptyTitle')}
              </h2>
              <p>{t('municipalComparison.emptyDescription')}</p>
            </div>
          )}
          {state === 'ready' && records.length > 0 && (
            <div className="space-y-8">
              <div className="grid gap-4 sm:grid-cols-3">
                <article className="summary-card">
                  <strong>{municipalityCount}</strong>
                  <span>{t('municipalComparison.municipalities')}</span>
                </article>
                <article className="summary-card">
                  <strong>{sectorCount}</strong>
                  <span>{t('municipalComparison.sectors')}</span>
                </article>
                <article className="summary-card">
                  <strong>{records.length}</strong>
                  <span>{t('municipalComparison.reviewedFacts')}</span>
                </article>
              </div>

              <div className="source-warning" role="note">
                <strong>{t('municipalComparison.evidenceBoundary')}</strong>
                <p className="mt-2">{evidenceNote}</p>
              </div>

              <MunicipalBudgetComparisonChart records={records} />

              <section className="comparison-panel">
                <h2 className="font-display text-2xl font-bold text-forest">
                  {t('municipalComparison.tableTitle')}
                </h2>
                <p className="mt-3 leading-7 text-muted">
                  {t('municipalComparison.tableDescription')}
                </p>
                <div className="mt-6 overflow-x-auto">
                  <table className="comparison-table">
                    <caption className="sr-only">{t('municipalComparison.tableCaption')}</caption>
                    <thead>
                      <tr>
                        <th>{t('municipalComparison.municipality')}</th>
                        <th>{t('municipalComparison.sector')}</th>
                        <th>{t('municipalComparison.allocated')}</th>
                        <th>{t('municipalComparison.spent')}</th>
                        <th>{t('municipalComparison.utilization')}</th>
                        <th>{t('municipalComparison.evidence')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {records.map((record) => {
                        const municipality = isNepali
                          ? record.local_government_name_np
                          : record.local_government_name_en
                        const sector = isNepali ? record.sector_name_np : record.sector_name_en
                        const scope = isNepali ? record.source_scope_np : record.source_scope_en
                        return (
                          <tr key={record.id}>
                            <td className="font-bold text-forest">{municipality}</td>
                            <td>{sector}</td>
                            <td>{formatNpr(record.allocated_amount)}</td>
                            <td>{formatNpr(record.spent_amount)}</td>
                            <td>{record.utilization_percent}%</td>
                            <td className="min-w-80">
                              <div className="flex flex-wrap gap-2">
                                <span className={`review-pill review-${record.reliability}`}>
                                  {t(`municipalComparison.reliability.${record.reliability}`)}
                                </span>
                                <span className={`review-pill compare-${record.comparability}`}>
                                  {t(
                                    `municipalComparison.comparability.${record.comparability}`,
                                  )}
                                </span>
                              </div>
                              <p className="mt-3 text-sm leading-6 text-muted">{scope}</p>
                              <Link
                                className="citation-link mt-3 inline-flex"
                                to={`/documents/${record.citation.document_id}?page=${record.citation.page}`}
                              >
                                {t('municipalComparison.openCitation', {
                                  page: record.citation.page,
                                })}
                              </Link>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          )}
        </section>
      </main>
      <SiteFooter />
    </div>
  )
}
