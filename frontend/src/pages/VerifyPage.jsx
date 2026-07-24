import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import {
  completeVerification,
  confirmMockVerification,
  getCurrentAccount,
  startMockVerification,
} from '../api/client'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

export default function VerifyPage() {
  const { t } = useTranslation()
  const [account, setAccount] = useState(null)
  const [stage, setStage] = useState('loading')
  const [identity, setIdentity] = useState({ phone: '', citizenship_number: '' })
  const [challenge, setChallenge] = useState(null)
  const [otp, setOtp] = useState('')
  const [error, setError] = useState(false)

  useEffect(() => {
    getCurrentAccount()
      .then((result) => {
        setAccount(result.data)
        if (!result.data.authenticated) setStage('guest')
        else if (result.data.identity_verified) setStage('success')
        else setStage('identity')
      })
      .catch(() => setStage('error'))
  }, [])

  const start = async (event) => {
    event.preventDefault()
    setError(false)
    try {
      const result = await startMockVerification(identity)
      setChallenge(result.data)
      setOtp(result.data.demo_otp || '')
      setStage('otp')
    } catch {
      setError(true)
    }
  }

  const confirm = async (event) => {
    event.preventDefault()
    setError(false)
    try {
      const confirmed = await confirmMockVerification({ challenge_id: challenge.challenge_id, otp })
      const completed = await completeVerification(confirmed.data.code)
      setAccount(completed.data)
      setStage('success')
    } catch {
      setError(true)
    }
  }

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <SiteHeader compact />
      <main className="page-shell py-14">
        <div className="mx-auto max-w-2xl">
          <p className="eyebrow">{t('verification.eyebrow')}</p>
          <h1 className="mt-4 font-display text-4xl font-bold text-forest">{t('verification.title')}</h1>
          <p className="mt-5 leading-7 text-muted">{t('verification.description')}</p>
          <p className="data-notice mt-6">{t('verification.mockBoundary')}</p>

          <section className="account-card mt-8">
            {stage === 'loading' && <p role="status">{t('common.loading')}</p>}
            {stage === 'guest' && <p><Link className="primary-action" to="/login">{t('verification.loginFirst')}</Link></p>}
            {stage === 'error' && <p role="alert">{t('verification.serviceError')}</p>}
            {stage === 'identity' && (
              <form className="space-y-5" onSubmit={start}>
                <label className="filter-field">
                  <span>{t('verification.phone')}</span>
                  <input autoComplete="tel" onChange={(event) => setIdentity((item) => ({ ...item, phone: event.target.value }))} required value={identity.phone} />
                </label>
                <label className="filter-field">
                  <span>{t('verification.citizenship')}</span>
                  <input onChange={(event) => setIdentity((item) => ({ ...item, citizenship_number: event.target.value }))} required value={identity.citizenship_number} />
                </label>
                <p className="text-xs leading-5 text-muted">{t('verification.demoCredentials')}</p>
                {error && <p className="source-warning" role="alert">{t('verification.matchError')}</p>}
                <button className="primary-action" type="submit">{t('verification.start')}</button>
              </form>
            )}
            {stage === 'otp' && (
              <form className="space-y-5" onSubmit={confirm}>
                <label className="filter-field">
                  <span>{t('verification.otp')}</span>
                  <input inputMode="numeric" onChange={(event) => setOtp(event.target.value)} required value={otp} />
                </label>
                {challenge.demo_otp && <p className="review-pill">{t('verification.demoOtp', { otp: challenge.demo_otp })}</p>}
                {error && <p className="source-warning" role="alert">{t('verification.otpError')}</p>}
                <button className="primary-action" type="submit">{t('verification.confirm')}</button>
              </form>
            )}
            {stage === 'success' && (
              <div>
                <span className="review-pill review-approved">{t('verification.verified')}</span>
                <h2 className="mt-5 font-display text-2xl font-bold text-forest">{t('verification.successTitle')}</h2>
                <p className="mt-3 leading-7 text-muted">{t('verification.successDescription', { username: account?.username })}</p>
                <Link className="primary-action mt-6" to="/budgets">{t('verification.browse')}</Link>
              </div>
            )}
          </section>
        </div>
      </main>
      <SiteFooter />
    </div>
  )
}
