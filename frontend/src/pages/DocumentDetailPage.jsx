import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { getDocument, getDocumentPage } from '../api/client'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

const formatNpr = (value, locale) => {
  if (value === null || value === undefined) return null
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'NPR',
    maximumFractionDigits: 0,
  }).format(Number(value))
}

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
  const metadataOnly = document.hosted_metadata_only
  const catalogEvidence = document.catalog_evidence || []
  const citedPages = [...new Set(catalogEvidence.map((item) => item.page_from).filter(Boolean))].sort(
    (left, right) => left - right,
  )
  const displayPage = metadataOnly && !searchParams.has('page') && citedPages.length
    ? citedPages[0]
    : requestedPage
  const citedPageIndex = citedPages.indexOf(displayPage)
  const matchingEvidence = catalogEvidence.filter((item) => {
    if (!item.page_from) return true
    return displayPage >= item.page_from && displayPage <= (item.page_to || item.page_from)
  })
  const visibleEvidence = matchingEvidence.length ? matchingEvidence : catalogEvidence
  const previousPage = metadataOnly
    ? citedPageIndex > 0 ? citedPages[citedPageIndex - 1] : null
    : requestedPage > 1 ? requestedPage - 1 : null
  const nextPage = metadataOnly
    ? citedPageIndex >= 0 && citedPageIndex < citedPages.length - 1
      ? citedPages[citedPageIndex + 1]
      : null
    : requestedPage < document.page_count ? requestedPage + 1 : null
  const municipality = isNepali && document.local_government_name_np
    ? document.local_government_name_np
    : document.local_government_name_en
  const sourceHost = (() => {
    try {
      return new URL(document.source_url).hostname
    } catch {
      return document.source_url
    }
  })()
  const locale = isNepali ? 'ne-NP' : 'en-NP'

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
                {metadataOnly
                  ? t('documents.status.official_link_registered')
                  : t(`documents.status.${document.processing_status}`)}
              </span>
            </div>
            <h1 className="mt-4 max-w-4xl font-display text-3xl font-bold text-forest sm:text-4xl">
              {title}
            </h1>
          </div>
        </section>

        <section className="page-shell py-8">
          <div className="document-viewer-grid">
            <div className={`document-preview${metadataOnly ? ' document-preview--catalog' : ''}`}>
              {document.file_url ? (
                <>
                  {document.file_format === 'image' ? (
                    <img
                      alt={t('documents.imageTitle', { title })}
                      src={document.file_url}
                    />
                  ) : (
                    <iframe
                      src={`${document.file_url}#page=${requestedPage}`}
                      title={t('documents.pdfTitle', { title, page: requestedPage })}
                    />
                  )}
                  <a
                    className="secondary-action mt-4"
                    href={document.file_url}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {t('documents.openPreserved')}
                  </a>
                </>
              ) : metadataOnly ? (
                <article className="official-source-record">
                  <p className="eyebrow">{t('documents.officialRecord')}</p>
                  <h2 className="mt-3 font-display text-2xl font-bold text-forest">
                    {t('documents.availableFrom', { municipality })}
                  </h2>
                  <p className="mt-3 leading-7 text-muted">{t('documents.metadataBoundary')}</p>
                  <dl className="source-record-grid mt-6">
                    <div>
                      <dt>{t('documents.sourceAuthority')}</dt>
                      <dd>{sourceHost}</dd>
                    </div>
                    <div>
                      <dt>{t('documents.fiscalYear')}</dt>
                      <dd>{document.fiscal_year_bs}</dd>
                    </div>
                    <div>
                      <dt>{t('documents.documentType')}</dt>
                      <dd>{t(`documents.type.${document.document_type}`)}</dd>
                    </div>
                    <div>
                      <dt>{t('documents.hostedAvailability')}</dt>
                      <dd>{t('documents.linkAvailable')}</dd>
                    </div>
                  </dl>
                  {document.source_note && (
                    <div className="source-record-note mt-6">
                      <p className="text-sm leading-6">{document.source_note}</p>
                    </div>
                  )}
                  <a
                    className="primary-action mt-6"
                    href={document.source_url}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {t('documents.source')}
                  </a>
                </article>
              ) : (
                <div className="empty-evidence">
                  <p>{t('documents.fileUnavailable')}</p>
                  <a className="primary-action mt-4" href={document.source_url} rel="noreferrer" target="_blank">
                    {t('documents.source')}
                  </a>
                </div>
              )}
            </div>

            <article className="extracted-page">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
                <div>
                  <p className="eyebrow">
                    {metadataOnly ? t('documents.catalogEvidence') : t('documents.extractedText')}
                  </p>
                  <h2 className="mt-2 font-display text-2xl font-bold text-forest">
                    {metadataOnly
                      ? t('documents.citedPage', { number: displayPage })
                      : t('documents.page', { number: requestedPage })}
                  </h2>
                </div>
                {page && (
                  <span className={`review-pill review-${page.review_status}`}>
                    {t(`documents.review.${page.review_status}`)}
                  </span>
                )}
              </div>
              {metadataOnly ? (
                visibleEvidence.length ? (
                  <div className="catalog-evidence-list mt-5">
                    {visibleEvidence.map((item, index) => {
                      const summary = isNepali && item.summary_np ? item.summary_np : item.summary_en
                      const section = isNepali && item.section_np ? item.section_np : item.section
                      const projectTitle = item.project && isNepali && item.project.title_np
                        ? item.project.title_np
                        : item.project?.title_en
                      return (
                        <section className="catalog-evidence-card" key={`${item.kind}-${item.page_from}-${index}`}>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="status-pill">
                              {t(`evidence.relationship.${item.relationship}`)}
                            </span>
                            {section && <span className="text-xs font-bold text-muted">{section}</span>}
                          </div>
                          <p className="mt-4 leading-7 text-ink">{summary}</p>
                          {item.kind === 'reviewed_budget_fact' && (
                            <dl className="catalog-money-grid mt-4">
                              <div>
                                <dt>{t('documents.allocated')}</dt>
                                <dd>{formatNpr(item.allocated_amount, locale)}</dd>
                              </div>
                              <div>
                                <dt>{t('documents.reportedSpent')}</dt>
                                <dd>{formatNpr(item.spent_amount, locale) || t('common.unknown')}</dd>
                              </div>
                            </dl>
                          )}
                          {item.project && (
                            <Link className="secondary-action mt-5" to={`/projects/${item.project.id}`}>
                              {t('documents.openRelatedProject')}: {projectTitle}
                            </Link>
                          )}
                        </section>
                      )
                    })}
                  </div>
                ) : (
                  <div className="empty-evidence mt-5">
                    <p>{t('documents.catalogNoCitation')}</p>
                    <p className="mt-2 text-xs leading-5">{t('documents.catalogNoCitationHelp')}</p>
                  </div>
                )
              ) : page ? (
                <>
                  <p className="mt-4 text-xs font-bold uppercase tracking-wide text-muted">
                    {t('documents.method')}: {t(`documents.methodValue.${page.extraction_method}`)}
                    {' · '}{t('documents.quality')}: {Math.round(Number(page.text_quality_score) * 100)}%
                  </p>
                  <pre className="extracted-text mt-5">{page.extracted_text}</pre>
                </>
              ) : (
                <div className="empty-evidence mt-5">
                  <p>{t('documents.pagePending')}</p>
                  <p className="mt-2 text-xs leading-5">{t('documents.pagePendingHelp')}</p>
                </div>
              )}
              {(!metadataOnly || citedPages.length > 1) && (
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
              )}
            </article>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  )
}
