import { useTranslation } from 'react-i18next'

function coverageTone(status) {
  if (
    [
      'amount_reported',
      'date_reported',
      'notice_reported',
      'award_reported',
      'reported',
      'percentage_reported',
    ].includes(status)
  ) {
    return 'verified'
  }
  if (['date_reported_amount_missing', 'status_reported_percentage_missing'].includes(status)) {
    return 'partial'
  }
  return 'missing'
}

function CoverageItem({ detail, label, status, t }) {
  const tone = coverageTone(status)
  return (
    <li className="coverage-item">
      <span aria-hidden="true" className={`coverage-dot coverage-dot--${tone}`} />
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <strong className="text-sm text-forest">{label}</strong>
          <span className={`coverage-status coverage-status--${tone}`}>
            {t(`project.coverage.status.${tone}`)}
          </span>
        </div>
        <p className="mt-1 text-xs leading-5 text-muted">{detail}</p>
      </div>
    </li>
  )
}

export default function ProjectEvidenceCoverage({ coverage, formatMoney, project }) {
  const { t } = useTranslation()
  if (!coverage) return null

  const rows = [
    {
      key: 'allocation',
      label: t('project.coverage.allocation'),
      status: coverage.allocation.status,
      detail:
        coverage.allocation.status === 'amount_reported'
          ? t('project.coverage.amountReported', {
              amount: formatMoney(coverage.allocation.amount),
            })
          : t('project.coverage.notFound'),
    },
    {
      key: 'agreement',
      label: t('project.coverage.agreement'),
      status: coverage.agreement.status,
      detail: coverage.agreement.date_bs
        ? t('project.coverage.dateReported', { date: coverage.agreement.date_bs })
        : t('project.coverage.agreementMissing'),
    },
    {
      key: 'monitoring',
      label: t('project.coverage.monitoring'),
      status: coverage.monitoring.status,
      detail: coverage.monitoring.date_bs
        ? t('project.coverage.dateReported', { date: coverage.monitoring.date_bs })
        : t('project.coverage.monitoringMissing'),
    },
    {
      key: 'procurement',
      label: t('project.coverage.procurement'),
      status: coverage.procurement.status,
      detail:
        coverage.procurement.status === 'notice_reported'
          ? t('project.coverage.procurementReported')
          : t('project.coverage.procurementMissing'),
    },
    {
      key: 'contract',
      label: t('project.coverage.contract'),
      status: coverage.contract_award.status,
      detail:
        coverage.contract_award.status === 'award_reported'
          ? t('project.coverage.contractReported')
          : t('project.coverage.contractMissing'),
    },
    {
      key: 'payment',
      label: t('project.coverage.payment'),
      status: coverage.payment.status,
      detail:
        coverage.payment.status === 'reported'
          ? t('project.coverage.amountReported', {
              amount: formatMoney(coverage.payment.amount),
            })
          : coverage.payment.status === 'date_reported_amount_missing'
            ? t('project.coverage.paymentDateOnly', { date: coverage.payment.date_bs })
            : t('project.coverage.paymentMissing'),
    },
    {
      key: 'progress',
      label: t('project.coverage.progress'),
      status: coverage.physical_progress.status,
      detail:
        coverage.physical_progress.status === 'percentage_reported'
          ? t('project.coverage.progressReported', {
              progress: coverage.physical_progress.percentage,
            })
          : coverage.physical_progress.status === 'status_reported_percentage_missing'
            ? t('project.coverage.progressStatusOnly', {
                status: t(`project.status.${coverage.physical_progress.project_status}`),
              })
            : t('project.coverage.progressMissing'),
    },
  ]
  const hasGaps = rows.some((row) => coverageTone(row.status) !== 'verified')

  return (
    <section className="evidence-coverage mt-8" aria-labelledby="evidence-coverage-title">
      <div>
        <p className="eyebrow">{t('project.coverage.eyebrow')}</p>
        <h2
          className="mt-3 font-display text-2xl font-bold text-forest"
          id="evidence-coverage-title"
        >
          {t('project.coverage.title')}
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
          {t('project.coverage.description')}
        </p>
      </div>

      <ul className="coverage-grid mt-6">
        {rows.map((row) => (
          <CoverageItem {...row} key={row.key} t={t} />
        ))}
      </ul>

      {hasGaps && (
        <div className="coverage-next mt-6">
          <div>
            <h3 className="font-display text-lg font-bold text-forest">
              {t('project.coverage.nextTitle')}
            </h3>
            <p className="mt-2 text-sm leading-6 text-muted">
              {t('project.coverage.nextDescription')}
            </p>
          </div>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-muted">
            {coverage.contract_award.status === 'not_found' && (
              <li>{t('project.coverage.required.contract')}</li>
            )}
            {coverage.payment.status !== 'reported' && (
              <li>{t('project.coverage.required.payment')}</li>
            )}
            {coverage.physical_progress.status !== 'percentage_reported' && (
              <li>{t('project.coverage.required.completion')}</li>
            )}
          </ul>
          <div className="mt-5 flex flex-wrap gap-3">
            <a className="primary-action" href="#project-evidence">
              {t('project.coverage.openCitation')}
            </a>
            {project.source_url && (
              <a
                className="secondary-action"
                href={project.source_url}
                rel="noreferrer"
                target="_blank"
              >
                {t('project.coverage.openOfficialCatalogue')}
              </a>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
