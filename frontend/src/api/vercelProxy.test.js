import { describe, expect, it } from 'vitest'

import { buildUpstreamUrl } from '../../api/proxy'

describe('Vercel service proxy', () => {
  it('builds an allowlisted backend URL while preserving filters', () => {
    const url = buildUpstreamUrl({
      __service: 'backend',
      __path: '/api/v1/projects/',
      municipality: 'PKR',
      fiscal_year: '2081-82',
    })

    expect(url?.origin).toBe('https://budget-darpan-api.onrender.com')
    expect(url?.pathname).toBe('/api/v1/projects/')
    expect(url?.searchParams.get('municipality')).toBe('PKR')
    expect(url?.searchParams.get('fiscal_year')).toBe('2081-82')
  })

  it('rejects unknown services and paths outside the public API', () => {
    expect(buildUpstreamUrl({
      __service: 'attacker-controlled-host',
      __path: '/api/v1/health/',
    })).toBeNull()
    expect(buildUpstreamUrl({
      __service: 'backend',
      __path: '/admin/',
    })).toBeNull()
    expect(buildUpstreamUrl({
      __service: 'backend',
      __path: '/api/v1/../admin/',
    })).toBeNull()
  })
})
