import { useTranslation } from 'react-i18next'
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const compactNpr = new Intl.NumberFormat('en-NP', {
  notation: 'compact',
  maximumFractionDigits: 1,
})

export default function MunicipalBudgetComparisonChart({ records }) {
  const { i18n, t } = useTranslation()
  const isNepali = i18n.resolvedLanguage === 'np'
  const chartData = records.map((record) => ({
    label: `${record.local_government_code} · ${record.sector_code}`,
    allocated: Number(record.allocated_amount),
    spent: Number(record.spent_amount),
    utilization: Number(record.utilization_percent),
    fullLabel: `${
      isNepali ? record.local_government_name_np : record.local_government_name_en
    } · ${isNepali ? record.sector_name_np : record.sector_name_en}`,
  }))

  return (
    <section className="comparison-panel" aria-labelledby="municipal-comparison-chart-title">
      <p className="eyebrow">{t('municipalComparison.chartEyebrow')}</p>
      <h2
        className="mt-2 font-display text-2xl font-bold text-forest"
        id="municipal-comparison-chart-title"
      >
        {t('municipalComparison.chartTitle')}
      </h2>
      <p className="mt-3 text-sm leading-6 text-muted">
        {t('municipalComparison.chartDescription')}
      </p>
      <div className="mt-7 h-96" aria-label={t('municipalComparison.chartLabel')} role="img">
        <ResponsiveContainer height="100%" width="100%">
          <ComposedChart data={chartData} margin={{ bottom: 24, left: 12, right: 18, top: 8 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" interval={0} />
            <YAxis tickFormatter={(value) => compactNpr.format(value)} width={72} yAxisId="money" />
            <YAxis domain={[0, 100]} orientation="right" tickFormatter={(value) => `${value}%`} width={48} yAxisId="percent" />
            <Tooltip
              formatter={(value, name) =>
                name === t('municipalComparison.utilization')
                  ? `${value}%`
                  : `NPR ${Number(value).toLocaleString('en-NP')}`
              }
              labelFormatter={(_, payload) => payload?.[0]?.payload?.fullLabel || ''}
            />
            <Legend />
            <Bar dataKey="allocated" fill="#2774b8" name={t('municipalComparison.allocated')} radius={[4, 4, 0, 0]} yAxisId="money" />
            <Bar dataKey="spent" fill="#e06c4f" name={t('municipalComparison.spent')} radius={[4, 4, 0, 0]} yAxisId="money" />
            <Line dataKey="utilization" dot={{ fill: '#d99124', r: 4 }} name={t('municipalComparison.utilization')} stroke="#d99124" strokeWidth={3} type="monotone" yAxisId="percent" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
