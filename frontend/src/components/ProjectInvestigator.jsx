import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { askInvestigator } from '../api/client'

const suggestionKeys = ['moneyJourney', 'payment', 'audit']

export default function ProjectInvestigator({ projectId }) {
  const { t } = useTranslation()
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [state, setState] = useState('idle')

  const submitQuestion = async (event) => {
    event?.preventDefault()
    const cleanedQuestion = question.trim()
    if (cleanedQuestion.length < 3) return
    setState('loading')
    setResult(null)
    try {
      const response = await askInvestigator({
        question: cleanedQuestion,
        projectId,
      })
      setResult(response.data)
      setState('ready')
    } catch {
      setState('error')
    }
  }

  const selectSuggestion = (key) => {
    setQuestion(t(`investigator.suggestions.${key}`))
    setResult(null)
    setState('idle')
  }

  return (
    <section className="border-t border-line bg-forest text-white" id="project-investigator">
      <div className="page-shell grid gap-10 py-14 lg:grid-cols-[0.72fr_1.28fr] lg:items-start">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#9bd3c5]">
            {t('investigator.eyebrow')}
          </p>
          <h2 className="mt-4 font-display text-3xl font-bold">
            {t('investigator.title')}
          </h2>
          <p className="mt-4 max-w-xl leading-7 text-[#d6e4df]">
            {t('investigator.description')}
          </p>
          <p className="mt-6 border-l-2 border-amber pl-4 text-sm leading-6 text-[#d6e4df]">
            {t('investigator.safety')}
          </p>
        </div>

        <div className="rounded-xl border border-white/15 bg-white p-5 text-ink shadow-2xl sm:p-7">
          <form onSubmit={submitQuestion}>
            <label className="font-bold text-forest" htmlFor="investigator-question">
              {t('investigator.questionLabel')}
            </label>
            <textarea
              className="mt-3 min-h-28 w-full resize-y rounded-lg border border-line bg-canvas px-4 py-3 leading-6 text-ink focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
              disabled={state === 'loading'}
              id="investigator-question"
              maxLength="1000"
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={t('investigator.placeholder')}
              value={question}
            />
            <div className="mt-3 flex flex-wrap gap-2" aria-label={t('investigator.suggestionLabel')}>
              {suggestionKeys.map((key) => (
                <button
                  className="rounded-full border border-line bg-surface px-3 py-2 text-xs font-bold text-teal hover:bg-canvas"
                  key={key}
                  onClick={() => selectSuggestion(key)}
                  type="button"
                >
                  {t(`investigator.suggestions.${key}`)}
                </button>
              ))}
            </div>
            <button
              className="primary-action mt-5 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={state === 'loading' || question.trim().length < 3}
              type="submit"
            >
              {state === 'loading' ? t('investigator.investigating') : t('investigator.submit')}
            </button>
          </form>

          <div aria-live="polite">
            {state === 'error' && (
              <p className="data-notice mt-6" role="alert">{t('investigator.error')}</p>
            )}
            {state === 'ready' && result && (
              <article className="mt-7 border-t border-line pt-6">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="status-pill">
                    {t(`investigator.routes.${result.route}`, { defaultValue: result.route })}
                  </span>
                  <span className="review-pill">
                    {t('investigator.language', { language: result.language })}
                  </span>
                </div>
                <h3 className="mt-5 font-display text-2xl font-bold text-forest">
                  {t('investigator.answerTitle')}
                </h3>
                <p className="mt-3 whitespace-pre-line leading-7 text-ink">{result.answer}</p>

                {result.citations.length > 0 && (
                  <div className="mt-7">
                    <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-muted">
                      {t('investigator.citationsTitle')}
                    </h4>
                    <div className="mt-3 grid gap-3">
                      {result.citations.map((citation) => (
                        <Link
                          className="rounded-lg border border-line bg-canvas p-4 text-left no-underline hover:border-teal"
                          key={`${citation.document_id}-${citation.relationship}-${citation.page}-${citation.source_kind}`}
                          to={citation.viewer_path}
                        >
                          <span className="review-pill mb-2">
                            {t(`investigator.sourceKind.${citation.source_kind}`, {
                              defaultValue: citation.source_kind,
                            })}
                          </span>
                          <span className="block font-bold text-forest">
                            {citation.document_title}
                          </span>
                          <span className="mt-1 block text-sm text-muted">
                            {t('investigator.citationPage', {
                              page: citation.page,
                              section: citation.section,
                            })}
                          </span>
                          {citation.excerpt && (
                            <span className="mt-2 block max-h-24 overflow-hidden text-sm leading-6 text-ink">
                              {citation.excerpt}
                            </span>
                          )}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}

                {result.limitations.length > 0 && (
                  <div className="data-notice mt-6">
                    <div>
                      <strong className="text-forest">{t('investigator.limitationsTitle')}</strong>
                      <ul className="mt-2 list-disc space-y-1 pl-5">
                        {result.limitations.map((limitation) => (
                          <li key={limitation.code}>{limitation.message}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
                <p className="mt-4 text-xs leading-5 text-muted">
                  {t('investigator.provenance', {
                    retrieval: result.provenance.document_retrieval,
                    generation: result.provenance.answer_generation,
                  })}
                </p>
              </article>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
