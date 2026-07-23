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
            <a className="nav-link" href="#money-trail">{t('navigation.moneyTrail')}</a>
            <Link className="nav-link" to="/documents">{t('navigation.documents')}</Link>
            <a className="nav-link" href="#principles">{t('navigation.principles')}</a>
            <a className="nav-link" href="#status">{t('navigation.status')}</a>
          </nav>
        )}

        <div className="flex items-center gap-2">
          {compact && (
            <Link className="nav-link hidden sm:inline" to="/documents">
              {t('navigation.documents')}
            </Link>
          )}
          <button className="language-button" onClick={changeLanguage} type="button">
            <span aria-hidden="true">अ</span>
            {isNepali ? 'English' : 'नेपाली'}
          </button>
        </div>
      </div>
    </header>
  )
}
