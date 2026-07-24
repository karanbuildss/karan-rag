import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

export default function MunicipalityEvidenceSummary({ evidence, formatMoney }) {
  const { i18n, t } = useTranslation()
  const isNepali = i18n.resolvedLanguage === 'np'
  const records = evidence?.records || []
  const note = isNepali
    ? evidence?.evidence_summary?.note_np
    : evidence?.evidence_summary?.note_en

  if (!records.length) return null

  return (
    <section className="comparison-panel" aria-labelledby="municipality-evidence-title">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">{t('discovery.municipalityEvidence.eyebrow')}</p>
          <h2
            className="mt-2 font-display text-3xl font-bold text-forest"
            id="municipality-evidence-title"
          >
            {t('discovery.municipalityEvidence.title')}
          </h2>
        </div>
        {evidence.fiscal_year && (
          <span className="status-pill">{evidence.fiscal_year.year_bs}</span>
        )}
      </div>
      <p className="mt-4 max-w-4xl leading-7 text-muted">
        {t('discovery.municipalityEvidence.description')}
      </p>
      <p className="source-warning mt-5">{note}</p>

      <div className="mt-6 overflow-x-auto">
        <table className="comparison-table">
          <caption className="sr-only">
            {t('discovery.municipalityEvidence.tableCaption')}
          </caption>
          <thead>
            <tr>
              <th>{t('discovery.municipalityEvidence.sector')}</th>
              <th>{t('discovery.municipalityEvidence.allocated')}</th>
              <th>{t('discovery.municipalityEvidence.spent')}</th>
              <th>{t('discovery.municipalityEvidence.utilization')}</th>
              <th>{t('discovery.municipalityEvidence.source')}</th>
            </tr>
          </thead>
          <tbody>
            {records.map((record) => (
              <tr key={record.id}>
                <td className="font-bold text-forest">
                  {record[isNepali ? 'sector_name_np' : 'sector_name_en']}
                </td>
                <td>{formatMoney(record.allocated_amount)}</td>
                <td>{formatMoney(record.spent_amount)}</td>
                <td>{record.utilization_percent}%</td>
                <td className="min-w-72">
                  <p className="text-sm leading-6 text-muted">
                    {record[isNepali ? 'source_scope_np' : 'source_scope_en']}
                  </p>
                  <Link
                    className="citation-link mt-3 inline-flex"
                    to={`/documents/${record.citation.document_id}?page=${record.citation.page}`}
                  >
                    {t('discovery.municipalityEvidence.openSource', {
                      page: record.citation.page,
                    })}
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
