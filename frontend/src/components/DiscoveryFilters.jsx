import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

const statuses = ['unknown', 'planned', 'procurement', 'implementation', 'delayed', 'completed', 'on_hold']

export default function DiscoveryFilters({ onChange, onClear, options, values }) {
  const { i18n, t } = useTranslation()
  const [search, setSearch] = useState(values.search)
  const isNepali = i18n.resolvedLanguage === 'np'
  const hasFilters = Object.values(values).some(Boolean)

  useEffect(() => setSearch(values.search), [values.search])

  const submitSearch = (event) => {
    event.preventDefault()
    onChange('search', search.trim())
  }

  return (
    <section aria-labelledby="discovery-filters-title" className="filter-panel">
      <div className="flex flex-col gap-3 border-b border-line pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">{t('discovery.filters.eyebrow')}</p>
          <h2 className="mt-2 font-display text-2xl font-bold text-forest" id="discovery-filters-title">
            {t('discovery.filters.title')}
          </h2>
        </div>
        <button className="filter-clear" disabled={!hasFilters} onClick={onClear} type="button">
          {t('discovery.filters.clear')}
        </button>
      </div>

      <form className="mt-5 grid gap-4 lg:grid-cols-[1.4fr_repeat(5,minmax(0,1fr))]" onSubmit={submitSearch}>
        <div className="filter-field lg:col-span-2">
          <label htmlFor="project-discovery-search">{t('discovery.filters.searchLabel')}</label>
          <div className="flex gap-2">
            <input
              className="min-w-0 flex-1"
              id="project-discovery-search"
              onChange={(event) => setSearch(event.target.value)}
              placeholder={t('discovery.filters.searchPlaceholder')}
              type="search"
              value={search}
            />
            <button className="filter-submit" type="submit">
              {t('discovery.filters.searchAction')}
            </button>
          </div>
        </div>

        <label className="filter-field">
          <span>{t('discovery.filters.municipality')}</span>
          <select onChange={(event) => onChange('municipality', event.target.value)} value={values.municipality}>
            <option value="">{t('discovery.filters.all')}</option>
            {options.localGovernments.map((item) => (
              <option key={item.code} value={item.code}>
                {item[isNepali ? 'name_np' : 'name_en']}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span>{t('discovery.filters.ward')}</span>
          <input
            inputMode="numeric"
            max="99"
            min="1"
            onChange={(event) => onChange('ward', event.target.value)}
            placeholder={t('discovery.filters.anyWard')}
            type="number"
            value={values.ward}
          />
        </label>

        <label className="filter-field">
          <span>{t('discovery.filters.fiscalYear')}</span>
          <select onChange={(event) => onChange('fiscalYear', event.target.value)} value={values.fiscalYear}>
            <option value="">{t('discovery.filters.all')}</option>
            {options.fiscalYears.map((item) => (
              <option key={item.code} value={item.code}>{item.year_bs}</option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span>{t('discovery.filters.sector')}</span>
          <select onChange={(event) => onChange('sector', event.target.value)} value={values.sector}>
            <option value="">{t('discovery.filters.all')}</option>
            {options.sectors.map((item) => (
              <option key={item.code} value={item.code}>
                {item[isNepali ? 'name_np' : 'name_en']}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span>{t('discovery.filters.status')}</span>
          <select onChange={(event) => onChange('status', event.target.value)} value={values.status}>
            <option value="">{t('discovery.filters.all')}</option>
            {statuses.map((status) => (
              <option key={status} value={status}>{t(`project.status.${status}`)}</option>
            ))}
          </select>
        </label>
      </form>
    </section>
  )
}
