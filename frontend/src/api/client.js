import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
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

export async function getProjectEvidence(projectId) {
  const response = await api.get(`/projects/${projectId}/evidence/`)
  return response.data
}

export async function askInvestigator({ question, projectId, language = 'auto' }) {
  const response = await api.post(
    '/investigator/query/',
    { question, project_id: projectId, language },
    { timeout: 65000 },
  )
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

export default api
