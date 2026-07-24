import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import BrandMark from './BrandMark'

export default function SiteHeader({ compact = false }) {
  const { i18n, t } = useTranslation()
  const isNepali = i18n.resolvedLanguage === 'np'

  const changeLanguage = async () => {
    const nextLanguage = isNepali ? 'en' : 'np'
    await i18n.changeLanguage(nextLanguage)
    document.documentElement.lang = nextLanguage
  }

  return (
    <header className="border-b border-line bg-canvas/95">
      <div className="page-shell flex min-h-18 items-center justify-between gap-6 py-3">
        <Link className="flex items-center gap-3" to="/" aria-label={t('brand.homeLabel')}>
          <BrandMark />
          <span>
            <span className="block font-display text-lg font-bold leading-none text-forest">
              {t('brand.name')}
            </span>
            <span className="mt-1 block text-xs font-semibold tracking-wide text-muted">
              {t('brand.tagline')}
            </span>
          </span>
        </Link>

        {!compact && (
          <nav aria-label={t('navigation.label')} className="hidden items-center gap-7 md:flex">
            <Link className="nav-link" to="/budgets">{t('navigation.projects')}</Link>
            <Link className="nav-link" to="/compare">{t('navigation.compare')}</Link>
            <Link className="nav-link" to="/map">{t('navigation.map')}</Link>
            <Link className="nav-link" to="/anomalies">{t('navigation.anomalies')}</Link>
            <Link className="nav-link" to="/documents">{t('navigation.documents')}</Link>
            <Link className="nav-link" to="/investigator">{t('navigation.investigator')}</Link>
          </nav>
        )}

        <div className="flex items-center gap-2">
          {compact && (
            <div className="hidden items-center gap-4 sm:flex">
              <Link className="nav-link" to="/budgets">{t('navigation.projects')}</Link>
              <Link className="nav-link" to="/documents">{t('navigation.documents')}</Link>
            </div>
          )}
          <button className="language-button" onClick={changeLanguage} type="button">
            <span aria-hidden="true">अ</span>
            {isNepali ? 'English' : 'नेपाली'}
          </button>
          <Link className="nav-link hidden lg:inline" to="/account">{t('navigation.account')}</Link>
          <Link className="nav-link hidden xl:inline" to="/history">{t('navigation.history')}</Link>
        </div>
      </div>
    </header>
  )
}
