import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'

import { loginAccount, registerAccount } from '../api/client'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

export default function LoginPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [state, setState] = useState('idle')

  const update = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setState('loading')
    try {
      if (mode === 'register') await registerAccount(form)
      else await loginAccount({ username: form.username, password: form.password })
      navigate('/verify')
    } catch {
      setState('error')
    }
  }

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <SiteHeader compact />
      <main className="page-shell grid gap-10 py-14 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
        <section>
          <p className="eyebrow">{t('account.eyebrow')}</p>
          <h1 className="mt-4 font-display text-4xl font-bold text-forest">{t('account.title')}</h1>
          <p className="mt-5 max-w-xl leading-7 text-muted">{t('account.description')}</p>
          <p className="data-notice mt-7">{t('account.boundary')}</p>
        </section>

        <section className="account-card">
          <div className="discovery-tabs" role="tablist" aria-label={t('account.modeLabel')}>
            {['login', 'register'].map((item) => (
              <button
                aria-selected={mode === item}
                className={mode === item ? 'discovery-tab discovery-tab-active' : 'discovery-tab'}
                key={item}
                onClick={() => { setMode(item); setState('idle') }}
                role="tab"
                type="button"
              >
                {t(`account.${item}`)}
              </button>
            ))}
          </div>
          <form className="mt-7 space-y-5" onSubmit={submit}>
            <label className="filter-field">
              <span>{t('account.username')}</span>
              <input autoComplete="username" name="username" onChange={update} required value={form.username} />
            </label>
            {mode === 'register' && (
              <label className="filter-field">
                <span>{t('account.email')}</span>
                <input autoComplete="email" name="email" onChange={update} type="email" value={form.email} />
              </label>
            )}
            <label className="filter-field">
              <span>{t('account.password')}</span>
              <input autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength="10" name="password" onChange={update} required type="password" value={form.password} />
            </label>
            {state === 'error' && <p className="source-warning" role="alert">{t('account.error')}</p>}
            <button className="primary-action" disabled={state === 'loading'} type="submit">
              {state === 'loading' ? t('account.working') : t(`account.${mode}Action`)}
            </button>
          </form>
          <Link className="back-link mt-6 inline-flex" to="/budgets">{t('account.continuePublic')}</Link>
        </section>
      </main>
      <SiteFooter />
    </div>
  )
}
