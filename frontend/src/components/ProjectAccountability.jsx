import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import {
  createFeedback,
  getAnomalies,
  getCurrentAccount,
  getFeedback,
  getFeedbackSummary,
  updateFeedback,
} from '../api/client'

const initialForm = {
  completion_rating: '3',
  quality_rating: '3',
  usefulness_rating: '3',
  allocation_fairness_rating: '3',
  comment: '',
  directly_observed: false,
}

const editableForm = (feedback) => ({
  completion_rating: String(feedback.completion_rating),
  quality_rating: String(feedback.quality_rating),
  usefulness_rating: String(feedback.usefulness_rating),
  allocation_fairness_rating: String(feedback.allocation_fairness_rating),
  comment: feedback.comment || '',
  directly_observed: Boolean(feedback.directly_observed),
})

function FeedbackSummary({ summary }) {
  const { t } = useTranslation()
  if (!summary) return null
  const groups = ['all_citizens', 'verified_citizens', 'verified_local_residents']
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {groups.map((group) => (
        <article className="summary-card" key={group}>
          <p className="text-xs font-bold uppercase tracking-wide text-muted">{t(`feedback.groups.${group}`)}</p>
          <p className="mt-3 font-display text-3xl font-bold text-forest">{summary[group].count}</p>
          <p className="mt-2 text-xs text-muted">{summary[group].average_completion === null ? t('feedback.noRating') : t('feedback.average', { value: Number(summary[group].average_completion).toFixed(1) })}</p>
        </article>
      ))}
    </div>
  )
}

function RatingField({ label, name, onChange, value }) {
  const { t } = useTranslation()
  return (
    <label className="filter-field">
      <span>{label}</span>
      <select name={name} onChange={onChange} value={value}>
        {[1, 2, 3, 4, 5].map((rating) => <option key={rating} value={rating}>{t('feedback.rating', { rating })}</option>)}
      </select>
    </label>
  )
}

export default function ProjectAccountability({ onAccountLoaded, projectId }) {
  const { i18n, t } = useTranslation()
  const [account, setAccount] = useState(null)
  const [summary, setSummary] = useState(null)
  const [flags, setFlags] = useState([])
  const [form, setForm] = useState(initialForm)
  const [existing, setExisting] = useState(null)
  const [submitState, setSubmitState] = useState('idle')
  const [idempotencyKey] = useState(() => globalThis.crypto?.randomUUID?.() || `feedback-${Date.now()}`)
  const isNepali = i18n.resolvedLanguage === 'np'

  const refreshSummary = () => getFeedbackSummary(projectId).then((result) => setSummary(result.data))

  useEffect(() => {
    Promise.all([
      getCurrentAccount(),
      getFeedback({ project: projectId, page_size: 100 }),
      getFeedbackSummary(projectId),
      getAnomalies({ project: projectId, status: 'active', page_size: 20 }),
    ]).then(([accountResult, feedbackResult, summaryResult, anomalyResult]) => {
      setAccount(accountResult.data)
      onAccountLoaded?.(accountResult.data)
      const owned = (feedbackResult.data || []).find((item) => item.can_edit)
      if (owned) {
        setExisting(owned)
        setForm(editableForm(owned))
      }
      setSummary(summaryResult.data)
      setFlags(anomalyResult.data || [])
    }).catch(() => {})
  }, [onAccountLoaded, projectId])

  const updateForm = (event) => {
    const { checked, name, type, value } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  const submit = async (event) => {
    event.preventDefault()
    setSubmitState('loading')
    const payload = {
      ...form,
      project: projectId,
      completion_rating: Number(form.completion_rating),
      quality_rating: Number(form.quality_rating),
      usefulness_rating: Number(form.usefulness_rating),
      allocation_fairness_rating: Number(form.allocation_fairness_rating),
    }
    try {
      const result = existing
        ? await updateFeedback(existing.id, payload)
        : await createFeedback(payload, idempotencyKey)
      setExisting(result.data)
      setSubmitState('success')
      await refreshSummary()
    } catch (error) {
      if (error.response?.status === 409 && error.response.data?.data) {
        setExisting(error.response.data.data)
        setForm(editableForm(error.response.data.data))
        setSubmitState('duplicate')
      } else setSubmitState('error')
    }
  }

  return (
    <section className="border-t border-line bg-surface" id="accountability">
      <div className="page-shell py-14">
        <p className="eyebrow">{t('accountability.eyebrow')}</p>
        <h2 className="mt-3 font-display text-3xl font-bold text-forest">{t('accountability.title')}</h2>
        <p className="mt-4 max-w-3xl leading-7 text-muted">{t('accountability.description')}</p>

        <div className="mt-8 grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <h3 className="font-display text-2xl font-bold text-forest">{t('anomalies.projectTitle')}</h3>
            <p className="mt-2 text-sm text-muted">{t('anomalies.safety')}</p>
            <div className="mt-5 space-y-3">
              {flags.length === 0 && <p className="empty-evidence">{t('anomalies.emptyProject')}</p>}
              {flags.map((flag) => (
                <article className="rounded-lg border border-line bg-white p-4" key={flag.id}>
                  <div className="flex items-center gap-2"><span className={`anomaly-severity anomaly-${flag.severity}`}>{t(`anomalies.severity.${flag.severity}`)}</span><span className="text-xs font-bold text-muted">{flag.rule_id}</span></div>
                  <h4 className="mt-3 font-bold text-forest">{flag[isNepali ? 'title_np' : 'title_en']}</h4>
                  <p className="mt-2 text-sm leading-6 text-muted">{flag[isNepali ? 'reason_np' : 'reason_en']}</p>
                </article>
              ))}
            </div>
            <Link className="secondary-action mt-5" to="/anomalies">{t('anomalies.viewAll')}</Link>
          </div>

          <div>
            <h3 className="font-display text-2xl font-bold text-forest">{t('feedback.title')}</h3>
            <div className="mt-5"><FeedbackSummary summary={summary} /></div>
            {!account?.authenticated && <p className="empty-evidence mt-5"><Link className="back-link" to={`/login?returnTo=${encodeURIComponent(`/projects/${projectId}#accountability`)}`}>{t('feedback.login')}</Link></p>}
            {account?.authenticated && !account.identity_verified && <p className="empty-evidence mt-5"><Link className="back-link" to={`/verify?returnTo=${encodeURIComponent(`/projects/${projectId}#accountability`)}`}>{t('feedback.verify')}</Link></p>}
            {account?.identity_verified && (
              <form className="account-card mt-5 space-y-4" onSubmit={submit}>
                <div className="grid gap-4 sm:grid-cols-2">
                  <RatingField label={t('feedback.completion')} name="completion_rating" onChange={updateForm} value={form.completion_rating} />
                  <RatingField label={t('feedback.quality')} name="quality_rating" onChange={updateForm} value={form.quality_rating} />
                  <RatingField label={t('feedback.usefulness')} name="usefulness_rating" onChange={updateForm} value={form.usefulness_rating} />
                  <RatingField label={t('feedback.fairness')} name="allocation_fairness_rating" onChange={updateForm} value={form.allocation_fairness_rating} />
                </div>
                <label className="filter-field"><span>{t('feedback.comment')}</span><textarea maxLength="2000" name="comment" onChange={updateForm} rows="4" value={form.comment} /></label>
                <label className="flex items-center gap-3 text-sm text-muted"><input checked={form.directly_observed} name="directly_observed" onChange={updateForm} type="checkbox" />{t('feedback.observed')}</label>
                {submitState === 'duplicate' && <p className="source-warning" role="status">{t('feedback.duplicate')}</p>}
                {submitState === 'success' && <p className="review-pill review-approved" role="status">{t('feedback.saved')}</p>}
                {submitState === 'error' && <p className="source-warning" role="alert">{t('feedback.error')}</p>}
                <button className="primary-action" disabled={submitState === 'loading'} type="submit">{existing ? t('feedback.update') : t('feedback.submit')}</button>
              </form>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
