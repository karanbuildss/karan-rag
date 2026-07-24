import { useTranslation } from 'react-i18next'
import { Link, NavLink } from 'react-router-dom'

const primaryLinks = [
  ['projects', '/budgets'],
  ['compare', '/compare'],
  ['map', '/map'],
  ['anomalies', '/anomalies'],
  ['documents', '/documents'],
  ['investigator', '/investigator'],
]

const navClassName = ({ isActive }) => `nav-link${isActive ? ' nav-link--active' : ''}`

export default function SiteHeader() {
  const { i18n, t } = useTranslation()
  const isNepali = i18n.resolvedLanguage === 'np'

  const changeLanguage = async () => {
    const nextLanguage = isNepali ? 'en' : 'np'
    await i18n.changeLanguage(nextLanguage)
    document.documentElement.lang = nextLanguage
  }

  return (
    <header className="site-header">
      <div className="page-shell site-header__inner">
        <Link className="site-logo-link" to="/" aria-label={t('brand.homeLabel')}>
          <img className="site-logo" src="/logo-codefest.svg" alt={t('brand.name')} />
        </Link>

        <nav aria-label={t('navigation.label')} className="site-primary-nav">
          {primaryLinks.map(([key, path]) => (
            <NavLink className={navClassName} key={key} to={path}>
              {t(`navigation.${key}`)}
            </NavLink>
          ))}
        </nav>

        <div className="site-header-actions">
          <button className="language-button" onClick={changeLanguage} type="button">
            <span aria-hidden="true">अ</span>
            {isNepali ? 'English' : 'नेपाली'}
          </button>
          <NavLink className={navClassName} to="/account">{t('navigation.account')}</NavLink>
          <NavLink className={navClassName} to="/history">{t('navigation.history')}</NavLink>
        </div>
      </div>
    </header>
  )
}
