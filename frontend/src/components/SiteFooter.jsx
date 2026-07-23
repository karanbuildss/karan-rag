import { useTranslation } from 'react-i18next'

export default function SiteFooter() {
  const { t } = useTranslation()

  return (
    <footer className="border-t border-line bg-forest text-white">
      <div className="page-shell flex flex-col gap-3 py-8 text-sm text-white/75 md:flex-row md:items-center md:justify-between">
        <p>{t('footer.description')}</p>
        <p>{t('footer.disclaimer')}</p>
      </div>
    </footer>
  )
}
