import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { getDocuments } from '../api/client'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

export default function DocumentLibraryPage() {
  const { i18n, t } = useTranslation()
  const [documents, setDocuments] = useState([])
  const [state, setState] = useState('loading')
  const isNepali = i18n.resolvedLanguage === 'np'
  const officialCount = documents.filter(
    (document) => document.data_classification === 'official',
  ).length
  const municipalityCount = new Set(documents.map((document) => document.local_government_code)).size

  useEffect(() => {
    let active = true
    getDocuments({ ordering: '-fiscal_year__code', page_size: 100 })
      .then((response) => {
        if (active) {
          setDocuments(response.data)
          setState('ready')
        }
      })
      .catch(() => active && setState('error'))
    return () => {
      active = false
    }
  }, [])

  return (
    <div className="flex min-h-screen flex-col bg-canvas text-ink">
      <SiteHeader compact />
      <main className="flex-1">
        <section className="border-b border-line bg-surface">
          <div className="page-shell py-12">
            <Link className="back-link" to="/">← {t('documents.back')}</Link>
            <p className="eyebrow mt-8">{t('documents.eyebrow')}</p>
            <h1 className="mt-4 max-w-3xl font-display text-4xl font-bold text-forest sm:text-5xl">
              {t('documents.title')}
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-muted">
              {t('documents.description')}
            </p>
          </div>
        </section>

        <section className="page-shell py-12">
          {state === 'loading' && <p role="status">{t('documents.loading')}</p>}
          {state === 'error' && <p role="alert">{t('documents.error')}</p>}
          {state === 'ready' && documents.length === 0 && (
            <p className="empty-evidence">{t('documents.empty')}</p>
          )}
          {state === 'ready' && documents.length > 0 && (
            <div className="mb-8 grid gap-4 sm:grid-cols-3">
              <article className="summary-card">
                <strong>{documents.length}</strong>
                <span>{t('documents.catalogued')}</span>
              </article>
              <article className="summary-card">
                <strong>{officialCount}</strong>
                <span>{t('documents.officialSources')}</span>
              </article>
              <article className="summary-card">
                <strong>{municipalityCount}</strong>
                <span>{t('documents.municipalities')}</span>
              </article>
            </div>
          )}
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {documents.map((document) => (
              <article className="document-card" key={document.id}>
                <div className="flex flex-wrap gap-2">
                  <span className="status-pill">
                    {t(`documents.type.${document.document_type}`)}
                  </span>
                  <span className={`review-pill review-${document.processing_status}`}>
                    {t(`documents.status.${document.processing_status}`)}
                  </span>
                  <span className="review-pill">
                    {document.data_classification === 'official'
                      ? t('project.classification.official')
                      : t('project.classification.syntheticDemo')}
                  </span>
                </div>
                <h2 className="mt-5 font-display text-xl font-bold text-forest">
                  {isNepali && document.title_np ? document.title_np : document.title_en}
                </h2>
                <p className="mt-3 text-sm leading-6 text-muted">
                  {isNepali
                    ? document.local_government_name_np
                    : document.local_government_name_en}{' '}
                  · {document.fiscal_year_bs} · {t('documents.pages', { count: document.page_count })}
                </p>
                {document.source_url_kind === 'landing_page' && (
                  <p className="source-warning mt-3">{t('documents.landingPageWarning')}</p>
                )}
                <p className="mt-3 line-clamp-3 text-xs leading-5 text-muted">
                  {document.source_note}
                </p>
                <div className="mt-6 flex flex-wrap gap-3">
                  <Link className="primary-action" to={`/documents/${document.id}`}>
                    {t('documents.inspect')}
                  </Link>
                  <a
                    className="secondary-action"
                    href={document.source_url}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {t('documents.source')}
                  </a>
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
