import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'

import { getCurrentAccount, logoutAccount } from '../api/client'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

export default function AccountPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [account, setAccount] = useState(null)
  const [state, setState] = useState('loading')

  useEffect(() => {
    getCurrentAccount().then((result) => {
      if (!result?.data || typeof result.data.authenticated !== 'boolean') {
        throw new Error('Invalid account response')
      }
      setAccount(result.data)
      setState('ready')
    }).catch(() => setState('error'))
  }, [])

  const signOut = async () => {
    await logoutAccount()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <SiteHeader compact />
      <main className="page-shell py-14">
        <p className="eyebrow">{t('accountPage.eyebrow')}</p>
        <h1 className="mt-4 font-display text-4xl font-bold text-forest">{t('accountPage.title')}</h1>
        {state === 'loading' && <p className="mt-8" role="status">{t('common.loading')}</p>}
        {state === 'error' && <p className="source-warning mt-8" role="alert">{t('accountPage.error')}</p>}
        {state === 'ready' && !account.authenticated && (
          <section className="account-card mt-8"><p>{t('accountPage.guest')}</p><Link className="primary-action mt-5" to="/login">{t('accountPage.signIn')}</Link></section>
        )}
        {state === 'ready' && account.authenticated && (
          <section className="account-card mt-8 max-w-2xl">
            <span className={account.identity_verified ? 'review-pill review-approved' : 'review-pill'}>{account.identity_verified ? t('accountPage.verified') : t('accountPage.unverified')}</span>
            <h2 className="mt-5 font-display text-2xl font-bold text-forest">{account.username}</h2>
            <p className="mt-2 text-muted">{t('accountPage.role', { role: account.role })}</p>
            <div className="mt-6 flex flex-wrap gap-3">
              {!account.identity_verified && <Link className="primary-action" to="/verify">{t('accountPage.verify')}</Link>}
              <Link className="secondary-action" to="/history">{t('accountPage.history')}</Link>
              {(account.is_staff || ['official', 'moderator', 'system_admin'].includes(account.role)) && <Link className="secondary-action" to="/admin-documents">{t('accountPage.review')}</Link>}
              <button className="secondary-action" onClick={signOut} type="button">{t('accountPage.signOut')}</button>
            </div>
          </section>
        )}
      </main>
      <SiteFooter />
    </div>
  )
}
