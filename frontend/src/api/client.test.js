import { describe, expect, it } from 'vitest'

import api from './client'

describe('API session security', () => {
  it('sends cookies and the CSRF header across local development ports', () => {
    expect(api.defaults.withCredentials).toBe(true)
    expect(api.defaults.withXSRFToken).toBe(true)
    expect(api.defaults.xsrfCookieName).toBe('csrftoken')
    expect(api.defaults.xsrfHeaderName).toBe('X-CSRFToken')
  })
})
