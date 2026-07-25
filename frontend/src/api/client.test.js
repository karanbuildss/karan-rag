import { describe, expect, it } from 'vitest'

import api, { rejectUnexpectedHtml, resolveApiBaseUrls } from './client'

describe('API session security', () => {
  it('sends cookies and the CSRF header across local development ports', () => {
    expect(api.defaults.withCredentials).toBe(true)
    expect(api.defaults.withXSRFToken).toBe(true)
    expect(api.defaults.xsrfCookieName).toBe('csrftoken')
    expect(api.defaults.xsrfHeaderName).toBe('X-CSRFToken')
  })

  it('uses same-origin Vercel proxies so browser session cookies are first-party', () => {
    expect(resolveApiBaseUrls({
      hostname: 'budget-darpan-nepal.vercel.app',
      apiUrl: 'https://budget-darpan-api.onrender.com/api/v1',
      identityUrl: 'https://budget-darpan-identity.onrender.com/api/v1',
    })).toEqual({
      api: '/api/v1',
      identity: '/identity/api/v1',
    })
  })

  it('keeps configured service URLs outside Vercel', () => {
    expect(resolveApiBaseUrls({
      hostname: 'localhost',
      apiUrl: 'http://localhost:8000/api/v1',
      identityUrl: 'http://localhost:8001/api/v1',
    })).toEqual({
      api: 'http://localhost:8000/api/v1',
      identity: 'http://localhost:8001/api/v1',
    })
  })

  it('rejects an HTML SPA fallback returned from an API route', () => {
    expect(() => rejectUnexpectedHtml({
      data: '<!doctype html>',
      headers: { 'content-type': 'text/html; charset=utf-8' },
    })).toThrow('instead of JSON')
  })
})
