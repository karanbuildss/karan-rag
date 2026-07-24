import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { getChatSessions, getCurrentAccount } from '../api/client'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

export default function HistoryPage() {
  const { t } = useTranslation()
  const [state, setState] = useState('loading')
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    getCurrentAccount().then((account) => {
      if (!account.data.authenticated) {
        setState('guest')
        return
      }
      getChatSessions().then((result) => {
        setSessions(result.data || [])
        setState('ready')
      }).catch(() => setState('error'))
    }).catch(() => setState('guest'))
  }, [])

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <SiteHeader />
      <main className="page-shell py-14">
        <p className="eyebrow">{t('history.eyebrow')}</p>
        <h1 className="mt-4 font-display text-4xl font-bold text-forest">{t('history.title')}</h1>
        <p className="mt-4 max-w-3xl leading-7 text-muted">{t('history.description')}</p>
        {state === 'loading' && <p className="mt-8" role="status">{t('common.loading')}</p>}
        {state === 'guest' && <p className="empty-evidence mt-8"><Link className="back-link" to="/login?returnTo=%2Fhistory">{t('history.login')}</Link></p>}
        {state === 'error' && <p className="source-warning mt-8" role="alert">{t('history.error')}</p>}
        {state === 'ready' && sessions.length === 0 && <p className="empty-evidence mt-8">{t('history.empty')}</p>}
        <div className="mt-8 space-y-5">
          {sessions.map((session) => (
            <article className="account-card" key={session.id}>
              <p className="eyebrow">{session.project_code || t('history.general')}</p>
              <h2 className="mt-2 font-display text-2xl font-bold text-forest">{session.title}</h2>
              <div className="mt-5 space-y-4">
                {session.messages.map((message) => (
                  <div className={message.role === 'assistant' ? 'rounded-lg bg-surface p-4' : 'rounded-lg border border-line p-4'} key={message.id}>
                    <strong className="text-xs uppercase tracking-wide text-teal">{t(`history.roles.${message.role}`)}</strong>
                    <p className="mt-2 whitespace-pre-line leading-7">{message.content}</p>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </main>
      <SiteFooter />
    </div>
  )
}
