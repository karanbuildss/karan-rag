import { useTranslation } from 'react-i18next'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

function shortNumber(value) {
  const number = Number(value)
  if (Math.abs(number) >= 1_000_000) return `${Number((number / 1_000_000).toFixed(1))}m`
  if (Math.abs(number) >= 1_000) return `${Number((number / 1_000).toFixed(0))}k`
  return `${number}`
}

export default function InvestigatorVisualization({ visualization }) {
  const { i18n, t } = useTranslation()
  const isNepali = i18n.resolvedLanguage === 'np'
  const rows = visualization.data
    .filter((row) => row.value !== null && row.value !== undefined)
    .map((row) => ({
      ...row,
      label: row[isNepali ? 'label_np' : 'label_en'],
      value: Number(row.value),
    }))
  const formatValue = (value) =>
    visualization.unit === 'NPR'
      ? new Intl.NumberFormat(isNepali ? 'ne-NP' : 'en-NP', {
        style: 'currency',
        currency: 'NPR',
        maximumFractionDigits: 0,
      }).format(value)
      : `${Number(value).toFixed(1)}%`

  if (!rows.length) return null

  return (
    <section className="mt-6 rounded-lg border border-line bg-canvas p-4">
      <p className="text-xs font-bold uppercase tracking-[0.12em] text-teal">
        {t('investigator.visualizationEyebrow')}
      </p>
      <h4 className="mt-2 font-display text-xl font-bold text-forest">
        {visualization[isNepali ? 'title_np' : 'title_en']}
      </h4>
      <div aria-hidden="true" className="mt-4 h-56 min-w-0">
        <ResponsiveContainer height="100%" width="100%">
          <BarChart data={rows} margin={{ left: 5, right: 5, top: 8 }}>
            <CartesianGrid stroke="#d8ddd7" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#5f6c69', fontSize: 11 }} />
            <YAxis tick={{ fill: '#5f6c69', fontSize: 11 }} tickFormatter={shortNumber} />
            <Tooltip formatter={(value) => formatValue(value)} />
            <Bar dataKey="value" fill="#196a60" radius={[5, 5, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-xs leading-5 text-muted">
        {visualization[isNepali ? 'boundary_np' : 'boundary_en']}
      </p>
      <ul className="sr-only">
        {rows.map((row) => <li key={row.key}>{row.label}: {formatValue(row.value)}</li>)}
      </ul>
    </section>
  )
}
