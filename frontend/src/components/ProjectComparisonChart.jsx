import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const projectPalette = ['#177e68', '#2774b8', '#e06c4f', '#8b5bb5', '#d99124', '#2f9da6']

export default function ProjectComparisonChart({ formatMoney, projects }) {
  const { i18n, t } = useTranslation()
  const isNepali = i18n.resolvedLanguage === 'np'
  const chartData = projects
    .filter((project) => project.allocated_amount !== null)
    .map((project) => ({
      code: project.code,
      title: project[isNepali ? 'title_np' : 'title_en'],
      allocated: Number(project.allocated_amount),
    }))

  return (
    <section className="comparison-panel">
      <div className="max-w-3xl">
        <p className="eyebrow">{t('discovery.compare.eyebrow')}</p>
        <h2 className="mt-3 font-display text-3xl font-bold text-forest">
          {t('discovery.compare.title')}
        </h2>
        <p className="mt-3 leading-7 text-muted">{t('discovery.compare.description')}</p>
      </div>

      {chartData.length ? (
        <div aria-hidden="true" className="mt-8 h-80 min-w-0">
          <ResponsiveContainer height="100%" width="100%">
            <BarChart data={chartData} margin={{ bottom: 35, left: 12, right: 12, top: 8 }}>
              <CartesianGrid stroke="#d8ddd7" strokeDasharray="3 3" vertical={false} />
              <XAxis angle={-12} dataKey="code" height={60} interval={0} textAnchor="end" tick={{ fill: '#5f6c69', fontSize: 11 }} />
              <YAxis tick={{ fill: '#5f6c69', fontSize: 11 }} tickFormatter={(value) => `${Math.round(value / 100000) / 10}m`} />
              <Tooltip formatter={(value) => formatMoney(value)} />
              <Bar dataKey="allocated" radius={[5, 5, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell fill={projectPalette[index % projectPalette.length]} key={entry.code} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="empty-evidence mt-7">{t('discovery.compare.noKnownValues')}</p>
      )}

      <div className="mt-8 overflow-x-auto">
        <table className="comparison-table">
          <caption className="sr-only">{t('discovery.compare.tableCaption')}</caption>
          <thead>
            <tr>
              <th>{t('discovery.compare.project')}</th>
              <th>{t('discovery.filters.fiscalYear')}</th>
              <th>{t('discovery.card.allocation')}</th>
              <th>{t('discovery.card.evidence')}</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((project) => (
              <tr key={project.id}>
                <td>
                  <Link className="font-bold text-forest hover:text-teal" to={`/projects/${project.id}`}>
                    {project[isNepali ? 'title_np' : 'title_en']}
                  </Link>
                  <span className="mt-1 block text-xs text-muted">{project.code}</span>
                </td>
                <td>{project.fiscal_year_code}</td>
                <td>{project.allocated_amount === null ? t('project.unknown') : formatMoney(project.allocated_amount)}</td>
                <td>{project.evidence_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
