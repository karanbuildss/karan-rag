import { useTranslation } from 'react-i18next'

import ProjectInvestigator from '../components/ProjectInvestigator'
import SiteFooter from '../components/SiteFooter'
import SiteHeader from '../components/SiteHeader'
import { DEMO_PROJECT_ID } from '../config'

export default function InvestigatorPage() {
  const { t } = useTranslation()
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <SiteHeader />
      <main>
        <section className="page-shell py-12">
          <p className="eyebrow">{t('investigator.standaloneEyebrow')}</p>
          <h1 className="mt-4 font-display text-4xl font-bold text-forest">{t('investigator.standaloneTitle')}</h1>
          <p className="mt-4 max-w-3xl leading-7 text-muted">{t('investigator.standaloneDescription')}</p>
        </section>
        <ProjectInvestigator projectId={DEMO_PROJECT_ID} />
      </main>
      <SiteFooter />
    </div>
  )
}
