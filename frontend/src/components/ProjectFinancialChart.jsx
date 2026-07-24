import { useTranslation } from 'react-i18next'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

function formatAxisValue(value) {
  const numericValue = Number(value)
  if (Math.abs(numericValue) >= 1_000_000) {
    return `${Number((numericValue / 1_000_000).toFixed(1))}m`
  }
  if (Math.abs(numericValue) >= 1_000) {
    return `${Number((numericValue / 1_000).toFixed(0))}k`
  }
  return `${numericValue}`
}

export default function ProjectFinancialChart({ formatMoney, summary }) {
  const { t } = useTranslation()
  const values = [
    {
      key: 'allocated',
      label: t('project.allocated'),
      value: summary.allocated_amount === null ? null : Number(summary.allocated_amount),
    },
    {
      key: 'contracted',
      label: t('project.contracted'),
      value: summary.contracted_amount === null ? null : Number(summary.contracted_amount),
    },
    {
      key: 'paid',
      label: t('project.reportedPaid'),
      value: summary.reported_paid_amount === null ? null : Number(summary.reported_paid_amount),
    },
  ]
  const chartValues = values.filter((item) => item.value !== null)

  if (chartValues.length === 0) {
    return (
      <div className="financial-chart-card">
        <p className="eyebrow">{t('project.chartEyebrow')}</p>
        <h2 className="mt-3 font-display text-2xl font-bold text-forest">
          {t('project.chartTitle')}
        </h2>
        <p className="mt-6 text-sm leading-6 text-muted">{t('project.chartEmpty')}</p>
      </div>
    )
  }

  return (
    <div className="financial-chart-card">
      <div>
        <p className="eyebrow">{t('project.chartEyebrow')}</p>
        <h2 className="mt-3 font-display text-2xl font-bold text-forest">
          {t('project.chartTitle')}
        </h2>
      </div>
      <div aria-hidden="true" className="mt-7 h-72 min-w-0">
        <ResponsiveContainer height="100%" width="100%">
          <BarChart data={chartValues} margin={{ left: 10, right: 10, top: 8 }}>
            <CartesianGrid stroke="#d8ddd7" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#5f6c69', fontSize: 12 }} />
            <YAxis
              tick={{ fill: '#5f6c69', fontSize: 11 }}
              tickFormatter={formatAxisValue}
            />
            <Tooltip formatter={(value) => formatMoney(value)} />
            <Bar dataKey="value" fill="#196a60" radius={[5, 5, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-xs leading-5 text-muted">{t('project.chartBoundary')}</p>
      <ul className="sr-only">
        {values.map((item) => (
          <li key={item.key}>
            {item.label}: {item.value === null ? t('project.unknown') : formatMoney(item.value)}
          </li>
        ))}
      </ul>
    </div>
  )
}
