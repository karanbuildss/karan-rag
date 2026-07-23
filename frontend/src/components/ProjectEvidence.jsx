import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { getProjectEvidence } from '../api/client'

export default function ProjectEvidence({ projectId, synthetic }) {
  const { i18n, t } = useTranslation()
  const [evidence, setEvidence] = useState([])
  const [state, setState] = useState('loading')
  const isNepali = i18n.resolvedLanguage === 'np'

  useEffect(() => {
    let active = true
    getProjectEvidence(projectId)
      .then((response) => {
        if (active) {
          setEvidence(response.data)
          setState('ready')
        }
      })
      .catch(() => active && setState('error'))
    return () => {
      active = false
    }
  }, [projectId])

  return (
    <section className="border-t border-line bg-surface" id="project-evidence">
      <div className="page-shell py-14">
        <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
          <div>
            <p className="eyebrow">{t('evidence.eyebrow')}</p>
            <h2 className="mt-3 font-display text-3xl font-bold text-forest">
              {t('evidence.title')}
            </h2>
            <p className="mt-3 max-w-2xl leading-7 text-muted">{t('evidence.description')}</p>
          </div>
          <Link className="secondary-action" to="/documents">
            {t('evidence.openLibrary')}
          </Link>
        </div>

        {synthetic && <p className="data-notice mt-6">{t('evidence.syntheticBoundary')}</p>}
        {state === 'loading' && <p className="mt-6 text-sm text-muted">{t('evidence.loading')}</p>}
        {state === 'error' && <p className="mt-6 text-sm text-muted">{t('evidence.error')}</p>}
        {state === 'ready' && evidence.length === 0 && (
          <p className="empty-evidence mt-6">{t('evidence.empty')}</p>
        )}
        {evidence.length > 0 && (
          <div className="mt-7 grid gap-4 md:grid-cols-2">
            {evidence.map((item) => (
              <article className="citation-card" key={`${item.document.id}-${item.relationship}`}>
                <span className="status-pill">{t(`evidence.relationship.${item.relationship}`)}</span>
                <h3 className="mt-4 font-display text-xl font-bold text-forest">
                  {isNepali && item.document.title_np
                    ? item.document.title_np
                    : item.document.title_en}
                </h3>
                <p className="mt-2 text-sm leading-6 text-muted">
                  {isNepali && item.evidence_note_np
                    ? item.evidence_note_np
                    : item.evidence_note_en}
                </p>
                <div className="mt-5 flex flex-wrap gap-3">
                  <Link
                    className="primary-action"
                    to={`/documents/${item.document.id}?page=${item.page_from || 1}`}
                  >
                    {t('evidence.openCitation')}
                  </Link>
                  <a
                    className="secondary-action"
                    href={item.document.source_url}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {t('evidence.officialSource')}
                  </a>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
