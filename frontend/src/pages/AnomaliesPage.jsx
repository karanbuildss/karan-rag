import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { getAnomalies } from '../api/client'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

function explanationText(item, isNepali) {
  if (typeof item === 'string') return item
  return item[isNepali ? 'np' : 'en'] || item.en || item.np
}

export default function AnomaliesPage() {
  const { i18n, t } = useTranslation()
  const [flags, setFlags] = useState([])
  const [state, setState] = useState('loading')
  const isNepali = i18n.resolvedLanguage === 'np'

  useEffect(() => {
    getAnomalies({ status: 'active', page_size: 100 })
      .then((result) => { setFlags(result.data || []); setState('ready') })
      .catch(() => setState('error'))
  }, [])

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <SiteHeader />
      <main>
        <section className="border-b border-line bg-surface">
          <div className="page-shell py-14">
            <p className="eyebrow">{t('anomalies.eyebrow')}</p>
            <h1 className="mt-4 max-w-4xl font-display text-4xl font-bold text-forest sm:text-5xl">{t('anomalies.title')}</h1>
            <p className="mt-5 max-w-3xl text-lg leading-8 text-muted">{t('anomalies.description')}</p>
            <p className="data-notice mt-7 max-w-3xl">{t('anomalies.safety')}</p>
          </div>
        </section>
        <section className="page-shell py-10">
          {state === 'loading' && <p role="status">{t('anomalies.loading')}</p>}
          {state === 'error' && <p role="alert">{t('anomalies.error')}</p>}
          {state === 'ready' && !flags.length && <p className="empty-evidence">{t('anomalies.empty')}</p>}
          <div className="space-y-5">
            {flags.map((flag) => (
              <article className="anomaly-card" key={flag.id}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`anomaly-severity anomaly-${flag.severity}`}>{t(`anomalies.severity.${flag.severity}`)}</span>
                  <span className="review-pill">{t(`anomalies.reliability.${flag.reliability}`)}</span>
                  {flag.project_data_classification === 'synthetic_demo' && (
                    <span className="classification-pill">{t('project.classification.syntheticDemo')}</span>
                  )}
                  <span className="text-xs font-bold text-muted">{flag.rule_id}</span>
                </div>
                <h2 className="mt-5 font-display text-2xl font-bold text-forest">{flag[isNepali ? 'title_np' : 'title_en']}</h2>
                <p className="mt-3 leading-7 text-muted">{flag[isNepali ? 'reason_np' : 'reason_en']}</p>
                <dl className="mt-5 grid gap-4 rounded-lg bg-surface p-4 text-sm sm:grid-cols-3">
                  <div><dt>{t('anomalies.dataUsed')}</dt><dd>{JSON.stringify(flag.data_used)}</dd></div>
                  <div><dt>{t('anomalies.threshold')}</dt><dd>{JSON.stringify(flag.threshold)}</dd></div>
                  <div><dt>{t('anomalies.calculation')}</dt><dd>{JSON.stringify(flag.calculated_values)}</dd></div>
                </dl>
                <h3 className="mt-5 font-bold text-forest">{t('anomalies.possibleExplanations')}</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">{flag.possible_explanations.map((item, index) => <li key={`${flag.id}-explanation-${index}`}>{explanationText(item, isNepali)}</li>)}</ul>
                <p className="mt-5 border-l-2 border-teal pl-4 text-sm leading-6 text-muted"><strong>{t('anomalies.recommendation')}:</strong> {flag[isNepali ? 'recommendation_np' : 'recommendation_en']}</p>
                <div className="mt-5 flex flex-wrap gap-3">
                  <Link className="secondary-action" to={`/projects/${flag.project}`}>{t('anomalies.openProject')}</Link>
                  {flag.source_references.map((source) => (
                    <span className="inline-flex items-center gap-2" key={`${source.document_id}-${source.page}`}>
                      <Link className="back-link" to={`/documents/${source.document_id}?page=${source.page || 1}`}>{t('anomalies.openSource', { page: source.page || '—' })}</Link>
                      {source.source_url && <a className="back-link" href={source.source_url} rel="noreferrer" target="_blank">{t('anomalies.openOfficialSource')}</a>}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  )
}
