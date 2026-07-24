import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import DiscoveryFilters from '../components/DiscoveryFilters'
import DiscoverySummary from '../components/DiscoverySummary'
import MunicipalityEvidenceSummary from '../components/MunicipalityEvidenceSummary'
import ProjectComparisonChart from '../components/ProjectComparisonChart'
import ProjectDiscoveryCard from '../components/ProjectDiscoveryCard'
import ProjectsMap from '../components/ProjectsMap'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'
import useProjectDiscovery from '../hooks/useProjectDiscovery'

const modes = [
  { key: 'list', path: '/budgets' },
  { key: 'compare', path: '/compare' },
  { key: 'map', path: '/map' },
]

export default function ProjectDiscoveryPage({ mode = 'list' }) {
  const { i18n, t } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()
  const { budgetEvidence, filters, options, projects, retry, state, summary } =
    useProjectDiscovery(searchParams)
  const isNepali = i18n.resolvedLanguage === 'np'
  const locale = isNepali ? 'ne-NP' : 'en-NP'
  const queryString = searchParams.toString()
  const hasMunicipalityEvidence = Boolean(budgetEvidence?.records?.length)

  const formatMoney = (value) => {
    if (value === null || value === undefined) return t('project.unknown')
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: 'NPR',
      maximumFractionDigits: 0,
    }).format(Number(value))
  }

  const updateFilter = (key, value) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next, { replace: true })
  }

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <SiteHeader />
      <main>
        <section className="border-b border-line bg-surface">
          <div className="page-shell py-12 sm:py-16">
            <p className="eyebrow">{t(`discovery.modes.${mode}.eyebrow`)}</p>
            <div className="mt-4 grid gap-6 lg:grid-cols-[1fr_22rem] lg:items-end">
              <div>
                <h1 className="max-w-4xl font-display text-4xl font-bold leading-tight text-forest sm:text-5xl">
                  {t(`discovery.modes.${mode}.title`)}
                </h1>
                <p className="mt-5 max-w-3xl text-lg leading-8 text-muted">
                  {t(`discovery.modes.${mode}.description`)}
                </p>
              </div>
              <p className="data-notice">{t('discovery.evidenceBoundary')}</p>
            </div>

            <nav aria-label={t('discovery.viewNavigation')} className="discovery-tabs mt-9">
              {modes.map((item) => (
                <Link
                  aria-current={item.key === mode ? 'page' : undefined}
                  className={item.key === mode ? 'discovery-tab discovery-tab-active' : 'discovery-tab'}
                  key={item.key}
                  to={`${item.path}${queryString ? `?${queryString}` : ''}`}
                >
                  {t(`discovery.tabs.${item.key}`)}
                </Link>
              ))}
            </nav>
          </div>
        </section>

        <div className="page-shell py-10">
          <DiscoveryFilters
            onChange={updateFilter}
            onClear={() => setSearchParams({}, { replace: true })}
            options={options}
            values={filters}
          />

          <div className="mt-8">
            {state === 'loading' && (
              <div className="discovery-state" role="status">
                <span className="loading-ring" aria-hidden="true" />
                <p>{t('discovery.loading')}</p>
              </div>
            )}

            {state === 'error' && (
              <section className="discovery-state" role="alert">
                <h2 className="font-display text-2xl font-bold text-forest">{t('discovery.errorTitle')}</h2>
                <p>{t('discovery.errorDescription')}</p>
                <button className="primary-action" onClick={retry} type="button">{t('project.retry')}</button>
              </section>
            )}

            {state === 'ready' && summary && (
              <>
                {projects.length > 0 || !hasMunicipalityEvidence ? (
                  <DiscoverySummary formatMoney={formatMoney} summary={summary} />
                ) : (
                  <MunicipalityEvidenceSummary
                    evidence={budgetEvidence}
                    formatMoney={formatMoney}
                  />
                )}

                <div className="mt-10 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <p className="eyebrow">
                      {t(
                        hasMunicipalityEvidence && !projects.length
                          ? 'discovery.municipalityEvidence.projectEyebrow'
                          : 'discovery.results.eyebrow',
                      )}
                    </p>
                    <h2 className="mt-2 font-display text-3xl font-bold text-forest">
                      {t(
                        hasMunicipalityEvidence && !projects.length
                          ? 'discovery.municipalityEvidence.projectTitle'
                          : 'discovery.results.count',
                        { count: projects.length },
                      )}
                    </h2>
                  </div>
                  <p className="text-sm text-muted">{t('discovery.results.unknownReminder')}</p>
                </div>

                {!projects.length && (
                  <p className="empty-evidence mt-7">
                    {t(
                      hasMunicipalityEvidence
                        ? 'discovery.municipalityEvidence.projectBoundary'
                        : 'discovery.empty',
                    )}
                  </p>
                )}

                {projects.length > 0 && mode === 'list' && (
                  <div className="mt-7 grid gap-5 lg:grid-cols-2">
                    {projects.map((project) => (
                      <ProjectDiscoveryCard formatMoney={formatMoney} key={project.id} project={project} />
                    ))}
                  </div>
                )}

                {projects.length > 0 && mode === 'compare' && (
                  <div className="mt-7">
                    <ProjectComparisonChart formatMoney={formatMoney} projects={projects} />
                  </div>
                )}

                {projects.length > 0 && mode === 'map' && (
                  <div className="mt-7">
                    <ProjectsMap projects={projects} />
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  )
}
