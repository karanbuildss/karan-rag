import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

export default function ProjectDiscoveryCard({ formatMoney, project }) {
  const { i18n, t } = useTranslation()
  const isNepali = i18n.resolvedLanguage === 'np'
  const title = project[isNepali ? 'title_np' : 'title_en']
  const municipality = project[isNepali ? 'local_government_name_np' : 'local_government_name_en']
  const subsector = project[isNepali ? 'subsector_name_np' : 'subsector_name_en']
  const note = project[isNepali ? 'data_note_np' : 'data_note_en']

  return (
    <article className="project-discovery-card">
      <div className="flex flex-wrap items-center gap-2">
        <span className="status-pill">{t(`project.status.${project.status}`)}</span>
        <span className="review-pill">{project.fiscal_year_code}</span>
      </div>
      <h2 className="mt-5 font-display text-2xl font-bold leading-tight text-forest">
        <Link className="hover:text-teal" to={`/projects/${project.id}`}>{title}</Link>
      </h2>
      <p className="mt-3 text-sm font-bold text-muted">
        {municipality} · {project.ward_number ? t('project.ward', { number: project.ward_number }) : t('discovery.card.wardUnknown')}
      </p>
      <p className="mt-2 text-sm text-muted">{subsector}</p>

      <dl className="mt-6 grid grid-cols-3 gap-3 border-y border-line py-4">
        <div>
          <dt>{t('discovery.card.allocation')}</dt>
          <dd>{project.allocated_amount === null ? t('project.unknown') : formatMoney(project.allocated_amount)}</dd>
        </div>
        <div>
          <dt>{t('discovery.card.evidence')}</dt>
          <dd>{project.evidence_count}</dd>
        </div>
        <div>
          <dt>{t('discovery.card.tenders')}</dt>
          <dd>{project.tender_count}</dd>
        </div>
      </dl>

      <p className="mt-4 line-clamp-3 text-sm leading-6 text-muted">{note}</p>
      <Link className="secondary-action mt-5" to={`/projects/${project.id}`}>
        {t('discovery.card.open')}
      </Link>
    </article>
  )
}
