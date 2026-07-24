import { lazy, Suspense, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams } from 'react-router-dom'

import { getProjectMoneyTrail } from '../api/client'
import ProjectEvidence from '../components/ProjectEvidence'
import ProjectInvestigator from '../components/ProjectInvestigator'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'

const ProjectFinancialChart = lazy(() => import('../components/ProjectFinancialChart'))
const ProjectMap = lazy(() => import('../components/ProjectMap'))

function MoneyCard({ label, note, value }) {
  return (
    <article className="money-card">
      <p className="text-xs font-bold uppercase tracking-[0.12em] text-muted">{label}</p>
      <p className="mt-3 font-display text-2xl font-bold text-forest sm:text-3xl">{value}</p>
      {note && <p className="mt-2 text-xs leading-5 text-muted">{note}</p>}
    </article>
  )
}

function TimelineItem({ children, date, index, title }) {
  return (
    <li className="grid grid-cols-[2.4rem_1fr] gap-3">
      <div className="flex flex-col items-center">
        <span className="journey-dot">{index}</span>
        <span className="min-h-8 flex-1 w-px bg-line" />
      </div>
      <div className="timeline-card mb-4">
        <div className="flex flex-col justify-between gap-1 sm:flex-row sm:items-start">
          <h3 className="font-display text-lg font-bold text-forest">{title}</h3>
          {date && <time className="text-xs font-bold text-muted">{date}</time>}
        </div>
        {children}
      </div>
    </li>
  )
}

export default function ProjectPage() {
  const { projectId } = useParams()
  const { i18n, t } = useTranslation()
  const [trail, setTrail] = useState(null)
  const [state, setState] = useState('loading')
  const [retryKey, setRetryKey] = useState(0)
  const isNepali = i18n.resolvedLanguage === 'np'
  const locale = isNepali ? 'ne-NP' : 'en-NP'

  useEffect(() => {
    let active = true
    setState('loading')

    getProjectMoneyTrail(projectId)
      .then((result) => {
        if (active) {
          setTrail(result.data)
          setState('ready')
        }
      })
      .catch(() => active && setState('error'))

    return () => {
      active = false
    }
  }, [projectId, retryKey])

  const formatMoney = (value) => {
    if (value === null || value === undefined) return t('project.unknown')
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: 'NPR',
      maximumFractionDigits: 0,
    }).format(Number(value))
  }

  const formatDate = (value) => {
    if (!value) return null
    return new Intl.DateTimeFormat(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(new Date(`${value}T00:00:00`))
  }

  const formatDateTime = (value) => {
    if (!value) return null
    return new Intl.DateTimeFormat(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      timeZone: 'Asia/Kathmandu',
      timeZoneName: 'short',
    }).format(new Date(value))
  }

  if (state === 'loading') {
    return (
      <div className="flex min-h-screen flex-col bg-canvas text-ink">
        <SiteHeader compact />
        <main className="page-shell flex flex-1 items-center justify-center py-24">
          <div className="text-center" role="status">
            <span className="loading-ring" aria-hidden="true" />
            <p className="mt-5 font-bold text-forest">{t('project.loading')}</p>
          </div>
        </main>
        <SiteFooter />
      </div>
    )
  }

  if (state === 'error' || !trail) {
    return (
      <div className="flex min-h-screen flex-col bg-canvas text-ink">
        <SiteHeader compact />
        <main className="page-shell flex flex-1 items-center justify-center py-24">
          <section className="max-w-lg text-center" role="alert">
            <p className="eyebrow">{t('project.errorEyebrow')}</p>
            <h1 className="mt-4 font-display text-3xl font-bold text-forest">
              {t('project.errorTitle')}
            </h1>
            <p className="mt-4 leading-7 text-muted">{t('project.errorDescription')}</p>
            <button className="primary-action mt-7" onClick={() => setRetryKey((key) => key + 1)}>
              {t('project.retry')}
            </button>
          </section>
        </main>
        <SiteFooter />
      </div>
    )
  }

  const project = trail.project
  const summary = trail.financial_summary
  const tenders = trail.procurement
  const award = trail.procurement.find((item) => item.award)?.award
  const title = isNepali ? project.title_np : project.title_en
  const description = isNepali ? project.description_np : project.description_en
  const municipality = isNepali
    ? project.local_government.name_np
    : project.local_government.name_en
  const dataNote = isNepali ? project.data_note_np : project.data_note_en
  const classificationKey = {
    official: 'official',
    reconstructed_from_official_sources: 'reconstructed',
    curated_demo: 'curatedDemo',
    synthetic_demo: 'syntheticDemo',
  }[project.data_classification]

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <SiteHeader compact />
      <main>
        <section className="border-b border-line bg-surface">
          <div className="page-shell py-10 sm:py-14">
            <Link className="back-link" to="/">← {t('project.back')}</Link>
            <div className="mt-7 flex flex-wrap items-center gap-3">
              <span className="status-pill">{t(`project.status.${project.status}`)}</span>
              <span className="classification-pill">
                {t(`project.classification.${classificationKey || 'unknown'}`)}
              </span>
            </div>
            <div className="mt-5 grid gap-8 lg:grid-cols-[1fr_18rem] lg:items-end">
              <div>
                <p className="eyebrow">
                  {municipality} · {t('project.ward', { number: project.ward_number })}
                </p>
                <h1 className="mt-4 max-w-4xl font-display text-4xl font-bold leading-tight text-forest sm:text-5xl">
                  {title}
                </h1>
                <p className="mt-5 max-w-3xl text-base leading-7 text-muted">{description}</p>
              </div>
              <div className="progress-panel">
                <div className="flex items-end justify-between gap-4">
                  <span className="text-sm font-bold text-muted">{t('project.officialProgress')}</span>
                  <strong className="font-display text-3xl text-forest">
                    {project.official_progress_percent ?? t('project.unknown')}
                    {project.official_progress_percent !== null && '%'}
                  </strong>
                </div>
                {project.official_progress_percent !== null && (
                  <div
                    aria-label={t('project.progressLabel', {
                      progress: project.official_progress_percent,
                    })}
                    aria-valuemax="100"
                    aria-valuemin="0"
                    aria-valuenow={project.official_progress_percent}
                    className="progress-track mt-4"
                    role="progressbar"
                  >
                    <span
                      className="progress-value"
                      style={{ width: `${project.official_progress_percent}%` }}
                    />
                  </div>
                )}
                <p className="mt-3 text-xs leading-5 text-muted">
                  {t('project.fiscalYear')} {project.fiscal_year.year_bs}
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="page-shell py-12">
          <p className="eyebrow">{t('project.financialEyebrow')}</p>
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MoneyCard label={t('project.allocated')} value={formatMoney(summary.allocated_amount)} />
            <MoneyCard label={t('project.contracted')} value={formatMoney(summary.contracted_amount)} />
            <MoneyCard
              label={t('project.reportedPaid')}
              note={t(`project.paymentStatus.${summary.payment_reporting_status}`)}
              value={formatMoney(summary.reported_paid_amount)}
            />
            <MoneyCard
              label={t('project.reportedBalance')}
              note={t('project.reportedBalanceNote')}
              value={formatMoney(summary.reported_contract_balance)}
            />
          </div>
          <div className="data-notice mt-5">
            <span aria-hidden="true" className="text-amber">◆</span>
            <p>{dataNote}</p>
          </div>
          <div className="mt-8">
            <Suspense fallback={<p role="status">{t('common.loadingVisualization')}</p>}>
              <ProjectFinancialChart formatMoney={formatMoney} summary={summary} />
            </Suspense>
          </div>
        </section>

        <section className="border-y border-line bg-white" id="project-money-trail">
          <div className="page-shell grid gap-12 py-14 lg:grid-cols-[0.68fr_1.32fr]">
            <div>
              <p className="eyebrow">{t('project.moneyTrailEyebrow')}</p>
              <h2 className="mt-4 font-display text-3xl font-bold text-forest">
                {t('project.moneyTrailTitle')}
              </h2>
              <p className="mt-4 leading-7 text-muted">{t('project.moneyTrailDescription')}</p>
              {award && (
                <div className="contractor-card mt-7">
                  <p className="text-xs font-bold uppercase tracking-[0.12em] text-muted">
                    {t('project.contractor')}
                  </p>
                  <p className="mt-2 font-display text-lg font-bold text-forest">
                    {award.contractor.name}
                  </p>
                  <p className="mt-2 text-xs text-muted">
                    {t('project.awardReference')}: {award.reference}
                  </p>
                </div>
              )}
            </div>

            <ol className="m-0 list-none p-0">
              <TimelineItem index="1" title={t('project.timeline.allocation')}>
                <p className="mt-2 text-sm leading-6 text-muted">
                  {formatMoney(summary.allocated_amount)} · {project.subsector[isNepali ? 'name_np' : 'name_en']}
                </p>
              </TimelineItem>
              <TimelineItem index="2" title={t('project.timeline.procurementNotice')}>
                {tenders.length ? (
                  <ul className="mt-3 space-y-3">
                    {tenders.map((tender) => (
                      <li className="rounded-xl border border-line bg-surface p-4" key={tender.reference}>
                        <strong className="block text-sm text-forest">
                          {isNepali ? tender.title_np : tender.title_en}
                        </strong>
                        <dl className="mt-3 grid gap-2 text-xs text-muted sm:grid-cols-2">
                          <div>
                            <dt className="font-bold">{t('project.tenderReference')}</dt>
                            <dd>{tender.reference}</dd>
                          </div>
                          <div>
                            <dt className="font-bold">{t('project.invitationNumber')}</dt>
                            <dd>{tender.invitation_number || t('project.unknown')}</dd>
                          </div>
                          <div>
                            <dt className="font-bold">{t('project.tenderEstimate')}</dt>
                            <dd>{formatMoney(tender.estimated_amount)}</dd>
                          </div>
                          <div>
                            <dt className="font-bold">{t('project.bidSecurity')}</dt>
                            <dd>{formatMoney(tender.bid_security_amount)}</dd>
                          </div>
                          <div className="sm:col-span-2">
                            <dt className="font-bold">{t('project.bidDeadline')}</dt>
                            <dd>{formatDateTime(tender.bid_submission_deadline) || t('project.unknown')}</dd>
                          </div>
                        </dl>
                        <p className="mt-3 text-xs leading-5 text-muted">
                          {isNepali ? tender.data_note_np : tender.data_note_en}
                        </p>
                        {tender.source_url && (
                          <a
                            className="mt-3 inline-flex text-xs font-bold text-teal underline-offset-4 hover:underline"
                            href={tender.source_url}
                            rel="noreferrer"
                            target="_blank"
                          >
                            {t('project.openTenderSource')}
                          </a>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-muted">{t('project.procurementNotReported')}</p>
                )}
              </TimelineItem>
              <TimelineItem
                date={formatDate(award?.awarded_date)}
                index="3"
                title={t('project.timeline.contractAward')}
              >
                <p className="mt-2 text-sm leading-6 text-muted">
                  {award
                    ? `${award.contractor.name} · ${formatMoney(award.contract_amount)}`
                    : t('project.awardNotReported')}
                </p>
              </TimelineItem>
              <TimelineItem index="4" title={t('project.timeline.reportedPayments')}>
                {trail.payments.length ? (
                  <ul className="mt-3 space-y-2">
                    {trail.payments.map((payment) => (
                      <li className="payment-row" key={payment.reference}>
                        <span>{isNepali ? payment.description_np : payment.description_en}</span>
                        <strong>{formatMoney(payment.amount)}</strong>
                        <time>{formatDate(payment.paid_on)}</time>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-muted">{t('project.notReported')}</p>
                )}
              </TimelineItem>
              <TimelineItem index="5" title={t('project.timeline.milestones')}>
                {trail.milestones.length ? (
                  <ul className="mt-3 space-y-2">
                    {trail.milestones.map((milestone) => (
                      <li className="milestone-row" key={milestone.sequence}>
                        <span>{isNepali ? milestone.title_np : milestone.title_en}</span>
                        <span>{t(`project.milestoneStatus.${milestone.status}`)}</span>
                        <strong>{milestone.progress_percent}%</strong>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-muted">{t('project.milestonesUnknown')}</p>
                )}
              </TimelineItem>
            </ol>
          </div>
        </section>

        <section className="page-shell py-12">
          <div className="grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
            <div>
              <p className="eyebrow">{t('project.mapEyebrow')}</p>
              <h2 className="mt-3 font-display text-3xl font-bold text-forest">
                {t('project.mapTitle')}
              </h2>
              <p className="mt-3 leading-7 text-muted">{t('project.mapDescription')}</p>
              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
                <div className="detail-cell">
                  <span>{t('project.projectCode')}</span>
                  <strong>{project.code}</strong>
                </div>
                <div className="detail-cell">
                  <span>{t('project.plannedCompletion')}</span>
                  <strong>{formatDate(project.planned_end_date) ?? t('project.unknown')}</strong>
                </div>
              </div>
            </div>
            <Suspense fallback={<p role="status">{t('common.loadingVisualization')}</p>}>
              <ProjectMap location={project.location} projectTitle={title} />
            </Suspense>
          </div>
        </section>
        <ProjectInvestigator projectId={projectId} />
        <ProjectEvidence
          projectId={projectId}
          synthetic={project.data_classification === 'synthetic_demo'}
        />
      </main>
      <SiteFooter />
    </div>
  )
}
