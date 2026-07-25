import axios from 'axios'

export function resolveApiBaseUrls({ hostname = '', apiUrl = '', identityUrl = '' } = {}) {
  const usesVercelProxy = hostname === 'vercel.app' || hostname.endsWith('.vercel.app')
  return {
    api: usesVercelProxy ? '/api/v1' : (apiUrl || 'http://localhost:8000/api/v1'),
    identity: usesVercelProxy
      ? '/identity/api/v1'
      : (identityUrl || 'http://localhost:8001/api/v1'),
  }
}

const deploymentUrls = resolveApiBaseUrls({
  hostname: typeof window === 'undefined' ? '' : window.location.hostname,
  apiUrl: import.meta.env.VITE_API_URL,
  identityUrl: import.meta.env.VITE_MOCK_IDENTITY_URL,
})

const api = axios.create({
  baseURL: deploymentUrls.api,
  headers: { Accept: 'application/json' },
  timeout: 5000,
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
})

const mockIdentityApi = axios.create({
  baseURL: deploymentUrls.identity,
  headers: { Accept: 'application/json' },
  timeout: 5000,
})

export async function getHealth() {
  const response = await api.get('/health/')
  return response.data
}

export async function getProjectMoneyTrail(projectId) {
  const response = await api.get(`/projects/${projectId}/money-trail/`)
  return response.data
}

export async function getProjects(params = {}) {
  const response = await api.get('/projects/', { params })
  return response.data
}

export async function getProjectDiscoverySummary(params = {}) {
  const response = await api.get('/projects/discovery-summary/', { params })
  return response.data
}

export async function getLocalGovernments(params = {}) {
  const response = await api.get('/local-governments/', { params })
  return response.data
}

export async function getFiscalYears(params = {}) {
  const response = await api.get('/fiscal-years/', { params })
  return response.data
}

export async function getSectors(params = {}) {
  const response = await api.get('/sectors/', { params })
  return response.data
}

export async function getBudgetComparison(params = {}) {
  const response = await api.get('/budget-allocations/comparison/', { params })
  return response.data
}

export async function getCsrfToken() {
  const response = await api.get('/auth/csrf/')
  return response.data
}

export async function registerAccount(payload) {
  await getCsrfToken()
  const response = await api.post('/auth/register/', payload)
  return response.data
}

export async function loginAccount(payload) {
  await getCsrfToken()
  const response = await api.post('/auth/login/', payload)
  return response.data
}

export async function logoutAccount() {
  const response = await api.post('/auth/logout/')
  return response.data
}

export async function getCurrentAccount() {
  const response = await api.get('/auth/me/')
  return response.data
}

export async function startMockVerification(payload) {
  const response = await mockIdentityApi.post('/verification/start/', payload)
  return response.data
}

export async function confirmMockVerification(payload) {
  const response = await mockIdentityApi.post('/verification/confirm/', payload)
  return response.data
}

export async function completeVerification(code) {
  const response = await api.post('/verification/complete/', { code })
  return response.data
}

export async function getAnomalies(params = {}) {
  const response = await api.get('/anomalies/', { params })
  return response.data
}

export async function getFeedbackSummary(projectId) {
  const response = await api.get('/feedback/summary/', { params: { project: projectId } })
  return response.data
}

export async function getFeedback(params = {}) {
  const response = await api.get('/feedback/', { params })
  return response.data
}

export async function createFeedback(payload, idempotencyKey) {
  const response = await api.post('/feedback/', payload, {
    headers: { 'Idempotency-Key': idempotencyKey },
  })
  return response.data
}

export async function updateFeedback(feedbackId, payload) {
  const response = await api.patch(`/feedback/${feedbackId}/`, payload)
  return response.data
}

export async function getProjectEvidence(projectId) {
  const response = await api.get(`/projects/${projectId}/evidence/`)
  return response.data
}

export async function askInvestigator({ question, projectId, language = 'auto', sessionId = null }) {
  const response = await api.post(
    '/investigator/query/',
    { question, project_id: projectId, language, session_id: sessionId },
    { timeout: 65000 },
  )
  return response.data
}

export async function getChatSessions() {
  const response = await api.get('/chat-sessions/')
  return response.data
}

export async function getDocuments(params = {}) {
  const response = await api.get('/documents/', { params })
  return response.data
}

export async function getDocument(documentId) {
  const response = await api.get(`/documents/${documentId}/`)
  return response.data
}

export async function getDocumentPage(documentId, pageNumber) {
  const response = await api.get(`/documents/${documentId}/pages/${pageNumber}/`)
  return response.data
}

export async function getDocumentReviewQueue() {
  const response = await api.get('/documents/review-queue/')
  return response.data
}

export async function reviewDocumentPage(documentId, pageNumber, decision) {
  const response = await api.post(`/documents/${documentId}/pages/${pageNumber}/review/`, { decision })
  return response.data
}

export default api
