import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { getDocument, getDocumentPage } from '../api/client'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

export default function DocumentDetailPage() {
  const { documentId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedPage = Math.max(1, Number(searchParams.get('page')) || 1)
  const { i18n, t } = useTranslation()
  const [document, setDocument] = useState(null)
  const [page, setPage] = useState(null)
  const [state, setState] = useState('loading')
  const isNepali = i18n.resolvedLanguage === 'np'

  useEffect(() => {
    let active = true
    setState('loading')
    getDocument(documentId)
      .then(async (response) => {
        const documentData = response.data
        let pageData = null
        const hasPage = documentData.pages.some((item) => item.page_number === requestedPage)
        if (hasPage) {
          pageData = (await getDocumentPage(documentId, requestedPage)).data
        }
        if (active) {
          setDocument(documentData)
          setPage(pageData)
          setState('ready')
        }
      })
      .catch(() => active && setState('error'))
    return () => {
      active = false
    }
  }, [documentId, requestedPage])

  const selectPage = (nextPage) => {
    setSearchParams({ page: String(nextPage) })
  }

  if (state !== 'ready' || !document) {
    return (
      <div className="flex min-h-screen flex-col bg-canvas text-ink">
        <SiteHeader compact />
        <main className="page-shell flex flex-1 items-center justify-center py-24">
          <p role={state === 'error' ? 'alert' : 'status'}>
            {state === 'error' ? t('documents.detailError') : t('documents.loading')}
          </p>
        </main>
        <SiteFooter />
      </div>
    )
  }

  const title = isNepali && document.title_np ? document.title_np : document.title_en
  const previousPage = requestedPage > 1 ? requestedPage - 1 : null
  const nextPage = requestedPage < document.page_count ? requestedPage + 1 : null

  return (
    <div className="flex min-h-screen flex-col bg-canvas text-ink">
      <SiteHeader compact />
      <main className="flex-1">
        <section className="border-b border-line bg-surface">
          <div className="page-shell py-9">
            <Link className="back-link" to="/documents">← {t('documents.backToLibrary')}</Link>
            <div className="mt-6 flex flex-wrap gap-2">
              <span className="status-pill">{document.fiscal_year_bs}</span>
              <span className={`review-pill review-${document.processing_status}`}>
                {t(`documents.status.${document.processing_status}`)}
              </span>
            </div>
            <h1 className="mt-4 max-w-4xl font-display text-3xl font-bold text-forest sm:text-4xl">
              {title}
            </h1>
          </div>
        </section>

        <section className="page-shell py-8">
          <div className="document-viewer-grid">
            <div className="document-preview">
              {document.file_url ? (
                <iframe
                  src={`${document.file_url}#page=${requestedPage}`}
                  title={t('documents.pdfTitle', { title, page: requestedPage })}
                />
              ) : (
                <div className="empty-evidence">
                  <p>{t('documents.fileUnavailable')}</p>
                  <a
                    className="primary-action mt-4"
                    href={document.source_url}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {t('documents.source')}
                  </a>
                </div>
              )}
            </div>

            <article className="extracted-page">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
                <div>
                  <p className="eyebrow">{t('documents.extractedText')}</p>
                  <h2 className="mt-2 font-display text-2xl font-bold text-forest">
                    {t('documents.page', { number: requestedPage })}
                  </h2>
                </div>
                {page && (
                  <span className={`review-pill review-${page.review_status}`}>
                    {t(`documents.review.${page.review_status}`)}
                  </span>
                )}
              </div>
              {page ? (
                <>
                  <p className="mt-4 text-xs font-bold uppercase tracking-wide text-muted">
                    {t('documents.method')}: {t(`documents.methodValue.${page.extraction_method}`)}
                    {' · '}{t('documents.quality')}: {Math.round(Number(page.text_quality_score) * 100)}%
                  </p>
                  <pre className="extracted-text mt-5">{page.extracted_text}</pre>
                </>
              ) : (
                <p className="empty-evidence mt-5">{t('documents.pagePending')}</p>
              )}
              <div className="mt-6 flex flex-wrap justify-between gap-3 border-t border-line pt-5">
                <button
                  className="secondary-action"
                  disabled={!previousPage}
                  onClick={() => previousPage && selectPage(previousPage)}
                  type="button"
                >
                  {t('documents.previous')}
                </button>
                <button
                  className="secondary-action"
                  disabled={!nextPage}
                  onClick={() => nextPage && selectPage(nextPage)}
                  type="button"
                >
                  {t('documents.next')}
                </button>
              </div>
            </article>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  )
}
