const UPSTREAMS = Object.freeze({
  backend: 'https://budget-darpan-api.onrender.com',
  identity: 'https://budget-darpan-identity.onrender.com',
})

const REQUEST_HEADERS_TO_SKIP = new Set([
  'accept-encoding',
  'connection',
  'content-length',
  'host',
  'transfer-encoding',
  'x-forwarded-for',
  'x-forwarded-host',
  'x-forwarded-proto',
])

const RESPONSE_HEADERS_TO_SKIP = new Set([
  'connection',
  'content-encoding',
  'content-length',
  'set-cookie',
  'transfer-encoding',
])

function firstQueryValue(value) {
  return Array.isArray(value) ? value[0] : value
}

export function buildUpstreamUrl(query) {
  const service = firstQueryValue(query.__service)
  const rawPath = firstQueryValue(query.__path)
  const upstream = UPSTREAMS[service]

  if (
    !upstream
    || typeof rawPath !== 'string'
    || !rawPath.startsWith('/api/v1/')
    || rawPath.includes('..')
  ) {
    return null
  }

  const parsedPath = new URL(rawPath, 'https://budget-darpan-proxy.invalid')
  if (
    parsedPath.origin !== 'https://budget-darpan-proxy.invalid'
    || !parsedPath.pathname.startsWith('/api/v1/')
  ) {
    return null
  }

  const url = new URL(`${parsedPath.pathname}${parsedPath.search}`, upstream)
  for (const [key, value] of Object.entries(query)) {
    if (key === '__service' || key === '__path') continue
    const values = Array.isArray(value) ? value : [value]
    for (const item of values) {
      if (item !== undefined && item !== null) url.searchParams.append(key, String(item))
    }
  }
  return url
}

function copyRequestHeaders(request) {
  const headers = new Headers()
  for (const [name, value] of Object.entries(request.headers || {})) {
    if (REQUEST_HEADERS_TO_SKIP.has(name.toLowerCase()) || value === undefined) continue
    headers.set(name, Array.isArray(value) ? value.join(', ') : String(value))
  }
  return headers
}

function requestBody(request) {
  if (request.method === 'GET' || request.method === 'HEAD' || request.body === undefined) return undefined
  if (typeof request.body === 'string' || Buffer.isBuffer(request.body)) return request.body
  return JSON.stringify(request.body)
}

function sendProxyError(response, status, code, message) {
  response.status(status).json({
    data: null,
    meta: {},
    errors: [{ code, message }],
  })
}

export default async function handler(request, response) {
  const upstreamUrl = buildUpstreamUrl(request.query || {})
  if (!upstreamUrl) {
    sendProxyError(response, 400, 'invalid_proxy_target', 'The requested service or path is invalid.')
    return
  }

  try {
    const upstreamResponse = await fetch(upstreamUrl, {
      method: request.method,
      headers: copyRequestHeaders(request),
      body: requestBody(request),
      redirect: 'manual',
      signal: AbortSignal.timeout(55000),
    })

    for (const [name, value] of upstreamResponse.headers.entries()) {
      if (!RESPONSE_HEADERS_TO_SKIP.has(name.toLowerCase())) response.setHeader(name, value)
    }

    const setCookies = upstreamResponse.headers.getSetCookie?.() || []
    if (setCookies.length) response.setHeader('set-cookie', setCookies)
    response.setHeader('cache-control', 'no-store')
    response.status(upstreamResponse.status).send(Buffer.from(await upstreamResponse.arrayBuffer()))
  } catch {
    sendProxyError(
      response,
      502,
      'upstream_unavailable',
      'The requested service is temporarily unavailable. Please retry shortly.',
    )
  }
}
