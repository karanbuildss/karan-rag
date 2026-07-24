import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { getCurrentAccount, getDocumentReviewQueue, reviewDocumentPage } from '../api/client'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

const allowedRoles = new Set(['official', 'moderator', 'system_admin'])

export default function AdminDocumentsPage() {
  const { t } = useTranslation()
  const [state, setState] = useState('loading')
  const [pages, setPages] = useState([])

  useEffect(() => {
    getCurrentAccount().then((account) => {
      if (!account.data.authenticated || (!account.data.is_staff && !allowedRoles.has(account.data.role))) {
        setState('forbidden')
        return
      }
      getDocumentReviewQueue().then((result) => {
        setPages(result.data || [])
        setState('ready')
      }).catch(() => setState('error'))
    }).catch(() => setState('forbidden'))
  }, [])

  const decide = async (page, decision) => {
    await reviewDocumentPage(page.document_id, page.page_number, decision)
    setPages((items) => items.filter((item) => !(item.document_id === page.document_id && item.page_number === page.page_number)))
  }

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <SiteHeader compact />
      <main className="page-shell py-14">
        <p className="eyebrow">{t('documentReview.eyebrow')}</p>
        <h1 className="mt-4 font-display text-4xl font-bold text-forest">{t('documentReview.title')}</h1>
        <p className="data-notice mt-6">{t('documentReview.boundary')}</p>
        {state === 'loading' && <p className="mt-8" role="status">{t('common.loading')}</p>}
        {state === 'forbidden' && <p className="empty-evidence mt-8"><Link className="back-link" to="/login?returnTo=%2Fadmin-documents">{t('documentReview.forbidden')}</Link></p>}
        {state === 'error' && <p className="source-warning mt-8" role="alert">{t('documentReview.error')}</p>}
        {state === 'ready' && pages.length === 0 && <p className="empty-evidence mt-8">{t('documentReview.empty')}</p>}
        <div className="mt-8 space-y-5">
          {pages.map((page) => (
            <article className="account-card" key={`${page.document_id}-${page.page_number}`}>
              <p className="eyebrow">{t('documentReview.page', { page: page.page_number })}</p>
              <h2 className="mt-2 font-display text-2xl font-bold text-forest">{page.document_title}</h2>
              <p className="mt-3 text-sm text-muted">{t('documentReview.quality', { score: page.text_quality_score })}</p>
              <pre className="mt-5 max-h-80 overflow-auto whitespace-pre-wrap rounded-lg border border-line bg-canvas p-4 font-sans text-sm leading-6">{page.extracted_text}</pre>
              <div className="mt-5 flex flex-wrap gap-3">
                <button className="primary-action" onClick={() => decide(page, 'approved')} type="button">{t('documentReview.approve')}</button>
                <button className="secondary-action" onClick={() => decide(page, 'rejected')} type="button">{t('documentReview.reject')}</button>
                <Link className="secondary-action" to={`/documents/${page.document_id}?page=${page.page_number}`}>{t('documentReview.open')}</Link>
              </div>
            </article>
          ))}
        </div>
      </main>
      <SiteFooter />
    </div>
  )
}
