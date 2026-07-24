import { lazy, Suspense, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'

import { getHealth } from './api/client'
import SiteFooter from './components/SiteFooter'
import SiteHeader from './components/SiteHeader'
import { DEMO_PROJECT_ID } from './config'

const DocumentDetailPage = lazy(() => import('./pages/DocumentDetailPage'))
const DocumentLibraryPage = lazy(() => import('./pages/DocumentLibraryPage'))
const AnomaliesPage = lazy(() => import('./pages/AnomaliesPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const ProjectDiscoveryPage = lazy(() => import('./pages/ProjectDiscoveryPage'))
const ProjectPage = lazy(() => import('./pages/ProjectPage'))
const VerifyPage = lazy(() => import('./pages/VerifyPage'))

const journeyKeys = ['allocation', 'project', 'payment', 'evidence']
const principleKeys = ['numbers', 'citations', 'anomalies']

function HomePage() {
  const { t } = useTranslation()
  const [apiStatus, setApiStatus] = useState('connecting')

  useEffect(() => {
    let active = true

    getHealth()
      .then(() => active && setApiStatus('connected'))
      .catch(() => active && setApiStatus('offline'))

    return () => {
      active = false
    }
  }, [])

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <SiteHeader />

      <main id="top">
        <section className="page-shell grid gap-12 pb-18 pt-16 lg:grid-cols-[1.12fr_0.88fr] lg:items-center lg:pb-24 lg:pt-22">
          <div>
            <p className="eyebrow">{t('hero.eyebrow')}</p>
            <h1 className="mt-5 max-w-4xl font-display text-5xl font-bold leading-[1.05] tracking-[-0.04em] text-forest sm:text-6xl">
              {t('hero.title')}
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-muted">{t('hero.description')}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link className="primary-action" to="/budgets">
                {t('hero.primaryAction')}
              </Link>
              <Link className="secondary-action" to={`/projects/${DEMO_PROJECT_ID}`}>
                {t('hero.projectAction')}
              </Link>
            </div>
            <p className="mt-8 flex max-w-2xl items-start gap-3 border-l-2 border-amber pl-4 text-sm leading-6 text-muted">
              <span aria-hidden="true" className="mt-0.5 text-amber">◆</span>
              {t('hero.safety')}
            </p>
          </div>

          <div className="evidence-panel" aria-label={t('visual.label')}>
            <div className="flex items-start justify-between gap-4 border-b border-line px-6 py-5">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal">
                  {t('visual.eyebrow')}
                </p>
                <h2 className="mt-2 font-display text-2xl font-bold text-forest">
                  {t('visual.title')}
                </h2>
              </div>
              <span className="status-pill">{t('visual.demoLabel')}</span>
            </div>
            <div className="space-y-0 px-6 py-4">
              {journeyKeys.map((key, index) => (
                <div className="grid grid-cols-[2.5rem_1fr] gap-3" key={key}>
                  <div className="flex flex-col items-center">
                    <span className="journey-dot">{index + 1}</span>
                    {index < journeyKeys.length - 1 && <span className="h-8 w-px bg-line" />}
                  </div>
                  <div className="pb-5">
                    <p className="font-bold text-ink">{t(`visual.steps.${key}.title`)}</p>
                    <p className="mt-1 text-sm leading-5 text-muted">
                      {t(`visual.steps.${key}.description`)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-y border-line bg-surface" id="money-trail">
          <div className="page-shell py-16">
            <p className="eyebrow">{t('journey.eyebrow')}</p>
            <div className="mt-4 grid gap-6 lg:grid-cols-[0.75fr_1.25fr] lg:gap-16">
              <h2 className="font-display text-3xl font-bold leading-tight text-forest sm:text-4xl">
                {t('journey.title')}
              </h2>
              <p className="text-lg leading-8 text-muted">{t('journey.description')}</p>
            </div>
          </div>
        </section>

        <section className="page-shell py-16" id="principles">
          <p className="eyebrow">{t('principles.eyebrow')}</p>
          <h2 className="mt-4 max-w-2xl font-display text-3xl font-bold text-forest sm:text-4xl">
            {t('principles.title')}
          </h2>
          <div className="mt-9 grid gap-5 md:grid-cols-3">
            {principleKeys.map((key, index) => (
              <article className="principle-card" key={key}>
                <span className="principle-number">0{index + 1}</span>
                <h3 className="mt-8 font-display text-xl font-bold text-forest">
                  {t(`principles.items.${key}.title`)}
                </h3>
                <p className="mt-3 text-sm leading-6 text-muted">
                  {t(`principles.items.${key}.description`)}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="page-shell pb-20" id="status">
          <div className="status-bar">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal">
                {t('status.eyebrow')}
              </p>
              <h2 className="mt-2 font-display text-2xl font-bold text-forest">
                {t('status.title')}
              </h2>
            </div>
            <div className={`connection connection-${apiStatus}`} role="status">
              <span aria-hidden="true" className="connection-dot" />
              {t(`status.${apiStatus}`)}
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  )
}

function RouteFallback() {
  const { t } = useTranslation()
  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas text-forest" role="status">
      {t('common.loading')}
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/documents" element={<DocumentLibraryPage />} />
          <Route path="/documents/:documentId" element={<DocumentDetailPage />} />
          <Route path="/budgets" element={<ProjectDiscoveryPage mode="list" />} />
          <Route path="/compare" element={<ProjectDiscoveryPage mode="compare" />} />
          <Route path="/map" element={<ProjectDiscoveryPage mode="map" />} />
          <Route path="/anomalies" element={<AnomaliesPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/verify" element={<VerifyPage />} />
          <Route path="/projects/:projectId" element={<ProjectPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App
