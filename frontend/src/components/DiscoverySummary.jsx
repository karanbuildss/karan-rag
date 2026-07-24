import { useTranslation } from 'react-i18next'

function SummaryCard({ detail, label, value }) {
  return (
    <article className="summary-card">
      <p className="text-xs font-bold uppercase tracking-[0.12em] text-muted">{label}</p>
      <p className="mt-3 font-display text-3xl font-bold text-forest">{value}</p>
      <p className="mt-2 text-xs leading-5 text-muted">{detail}</p>
    </article>
  )
}
export default function DiscoverySummary({ formatMoney, summary }) {
  const { t } = useTranslation()
  if (!summary) return null
  const totals = summary.totals

  return (
    <section aria-label={t('discovery.summary.label')} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <SummaryCard
        detail={t('discovery.summary.projectDetail')}
        label={t('discovery.summary.projects')}
        value={totals.project_count}
      />
      <SummaryCard
        detail={t('discovery.summary.allocationDetail', {
          count: totals.known_allocation_count,
          total: totals.project_count,
        })}
        label={t('discovery.summary.knownAllocation')}
        value={totals.allocated_total === null ? t('project.unknown') : formatMoney(totals.allocated_total)}
      />
      <SummaryCard
        detail={t('discovery.summary.evidenceDetail')}
        label={t('discovery.summary.evidence')}
        value={`${totals.evidence_project_count}/${totals.project_count}`}
      />
      <SummaryCard
        detail={t('discovery.summary.reportingDetail', {
          procurement: totals.procurement_project_count,
          payments: totals.payment_reported_project_count,
        })}
        label={t('discovery.summary.unknownAllocation')}
        value={totals.unknown_allocation_count}
      />
    </section>
  )
}
