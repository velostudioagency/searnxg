const BASE = import.meta.env.VITE_API_URL || ''

function adminHeaders() {
  const key = localStorage.getItem('searnxg.adminKey')
  return key ? { 'X-Admin-Key': key } : {}
}

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...adminHeaders(),
      ...(options.headers || {}),
    },
  })

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const message =
      typeof payload === 'string' ? payload : payload?.detail || 'Request failed'
    throw new Error(message)
  }
  return payload
}

export const api = {
  health: () => request('/api/health'),
  config: () => request('/api/config'),
  setup: () => request('/api/setup'),
  quickSetup: () => request('/api/setup/quick', { method: 'POST', body: '{}' }),
  setupSearxng: (url) =>
    request('/api/setup/searxng', { method: 'POST', body: JSON.stringify({ url }) }),

  search: (params) =>
    request('/api/ui/search', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  extract: (url) =>
    request('/api/extract', {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),

  getSettings: () => request('/api/settings'),
  updateSettings: (settings) =>
    request('/api/settings', {
      method: 'PUT',
      body: JSON.stringify({ settings }),
    }),
  testSearxng: (url, format) =>
    request('/api/settings/test-searxng', {
      method: 'POST',
      body: JSON.stringify({ url, format }),
    }),

  listKeys: () => request('/api/keys'),
  createKey: () => request('/api/keys', { method: 'POST', body: '{}' }),
  deleteKey: (key) =>
    request(`/api/keys/${encodeURIComponent(key)}`, { method: 'DELETE' }),

  openaiTools: () => request('/api/tools/openai'),
  mcpConfig: () => request('/api/tools/mcp'),
}

export const API_BASE = BASE || (typeof window !== 'undefined' ? window.location.origin : '')
