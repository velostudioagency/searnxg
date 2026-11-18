import React from 'react'
import { Icon } from './Icons.jsx'

function Toggle({ checked, onChange, label, description, disabled }) {
  return (
    <label className={`toggle-row ${disabled ? 'disabled' : ''}`}>
      <div className="toggle-copy">
        <span className="toggle-label">{label}</span>
        {description && <span className="toggle-desc">{description}</span>}
      </div>
      <input type="checkbox" checked={!!checked} onChange={(e) => onChange(e.target.checked)} disabled={disabled} />
      <span className="switch" aria-hidden="true" />
    </label>
  )
}

function Field({ label, hint, children }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  )
}

const LANGUAGES = [
  ['en', 'English'], ['es', 'Español'], ['fr', 'Français'], ['de', 'Deutsch'],
  ['it', 'Italiano'], ['pt', 'Português'], ['ja', '日本語'], ['zh', '中文'], ['ru', 'Русский'],
]

export default function SettingsPanel({
  draft,
  setDraft,
  onSave,
  saving,
  dirty,
  onTest,
  testing,
  testResult,
  keys,
  onCreateKey,
  onDeleteKey,
  onCopyKey,
  adminKey,
  setAdminKey,
  config,
  theme,
  setTheme,
}) {
  const update = (key, value) => setDraft((prev) => ({ ...prev, [key]: value }))
  const updateProvider = (name, value) =>
    setDraft((prev) => ({ ...prev, providers: { ...prev.providers, [name]: value } }))

  const sourceOrder = ['searxng', 'bing', 'duckduckgo', 'wikipedia', 'hackernews', 'github']

  return (
    <div className="settings-page">
      <div className="page-heading">
        <div>
          <h1>Settings</h1>
          <p>Configure search sources, API access and how the app behaves. Changes are saved to <code>backend/data/settings.json</code>.</p>
        </div>
      </div>

      <div className="settings-grid">
        {/* SearXNG connection */}
        <section className="settings-card wide">
          <div className="card-head"><span className="card-icon indigo"><Icon name="database" size={18} /></span>
            <div><h2>SearXNG connection</h2><p>Point this at your own SearXNG instance for metasearch. Optional. Built-in sources work without it.</p></div>
          </div>
          <div className="card-body form-grid">
            <Field label="Instance URL" hint="e.g. http://localhost:8080. Enable JSON format in SearXNG settings for best results.">
              <input
                value={draft.searxng_url || ''}
                onChange={(e) => update('searxng_url', e.target.value)}
                placeholder="http://localhost:8080"
              />
            </Field>
            <Field label="Response format">
              <select value={draft.searxng_format || 'auto'} onChange={(e) => update('searxng_format', e.target.value)}>
                <option value="auto">Auto (JSON, then HTML)</option>
                <option value="json">JSON only</option>
                <option value="html">HTML only</option>
              </select>
            </Field>
            <Field label="Instance API key (optional)">
              <input
                type="password"
                value={draft.searxng_api_key || ''}
                onChange={(e) => update('searxng_api_key', e.target.value)}
                placeholder="Sent as X-API-Key / Bearer token"
              />
            </Field>
            <div className="field field-action">
              <span className="field-label">&nbsp;</span>
              <button className="btn secondary" onClick={onTest} disabled={testing || !(draft.searxng_url || '').trim()}>
                {testing ? <span className="spinner" /> : <Icon name="bolt" size={15} />}
                {testing ? 'Testing…' : 'Test connection'}
              </button>
            </div>
          </div>
          {testResult && (
            <div className={`test-result ${testResult.ok ? 'ok' : 'bad'}`}>
              <Icon name={testResult.ok ? 'check' : 'info'} size={15} /> {testResult.message}
            </div>
          )}
        </section>

        {/* Search providers */}
        <section className="settings-card wide">
          <div className="card-head"><span className="card-icon tinted"><Icon name="globe" size={18} /></span>
            <div><h2>Search sources</h2><p>Enable or disable the providers used when searching.</p></div>
          </div>
          <div className="card-body toggle-grid">
            {sourceOrder.map((name) => (
              <Toggle
                key={name}
                checked={draft.providers?.[name]}
                onChange={(v) => updateProvider(name, v)}
                label={config?.provider_labels?.[name] || name}
                description={
                  name === 'searxng'
                    ? (draft.searxng_url ? 'Using your configured instance' : 'Requires an instance URL above')
                    : name === 'github' ? 'Repository search for the Code tab'
                    : name === 'hackernews' ? 'Tech news and discussions'
                    : 'No API key required'
                }
              />
            ))}
          </div>
        </section>

        {/* Defaults */}
        <section className="settings-card">
          <div className="card-head"><span className="card-icon tinted"><Icon name="search" size={18} /></span>
            <div><h2>Search defaults</h2><p>Applied when a request doesn't specify a value.</p></div>
          </div>
          <div className="card-body form-grid one-col">
            <Field label="Default result count">
              <input type="number" min="1" max="100" value={draft.default_limit ?? 10} onChange={(e) => update('default_limit', Number(e.target.value))} />
            </Field>
            <Field label="Maximum result count">
              <input type="number" min="1" max="200" value={draft.max_limit ?? 50} onChange={(e) => update('max_limit', Number(e.target.value))} />
            </Field>
            <Field label="Language">
              <select value={draft.language || 'en'} onChange={(e) => update('language', e.target.value)}>
                {LANGUAGES.map(([code, label]) => <option key={code} value={code}>{label}</option>)}
              </select>
            </Field>
            <Field label="Time range">
              <select value={draft.time_range || ''} onChange={(e) => update('time_range', e.target.value)}>
                <option value="">Any time</option>
                <option value="day">Past day</option>
                <option value="week">Past week</option>
                <option value="month">Past month</option>
                <option value="year">Past year</option>
              </select>
            </Field>
            <Field label="Request timeout (seconds)">
              <input type="number" min="1" max="60" step="0.5" value={draft.timeout ?? 12} onChange={(e) => update('timeout', Number(e.target.value))} />
            </Field>
            <Field label="Cache TTL (seconds)" hint="0 disables caching.">
              <input type="number" min="0" max="86400" value={draft.cache_ttl ?? 300} onChange={(e) => update('cache_ttl', Number(e.target.value))} />
            </Field>
            <Toggle checked={draft.safesearch} onChange={(v) => update('safesearch', v)} label="Safe search by default" />
          </div>
        </section>

        {/* API & security */}
        <section className="settings-card">
          <div className="card-head"><span className="card-icon tinted"><Icon name="shield" size={18} /></span>
            <div><h2>API &amp; security</h2><p>Control who can call the backend.</p></div>
          </div>
          <div className="card-body toggle-grid">
            <Toggle
              checked={draft.require_api_key}
              onChange={(v) => update('require_api_key', v)}
              label="Require API key for /api/search &amp; /api/extract"
              description="The browser UI uses a separate rate-limited endpoint and keeps working."
            />
            <Toggle checked={draft.enable_extract} onChange={(v) => update('enable_extract', v)} label="Enable page extraction" description="The fetch_url / extract tools." />
            <Toggle checked={draft.enable_mcp} onChange={(v) => update('enable_mcp', v)} label="Enable MCP server" description="Exposes web_search, fetch_url and list_sources tools." />
            <Field label="Max extracted characters">
              <input type="number" min="500" max="100000" step="500" value={draft.max_extract_chars ?? 12000} onChange={(e) => update('max_extract_chars', Number(e.target.value))} />
            </Field>
            <Field label="Admin key" hint="Protects /api/settings and key management. Leave empty for open access.">
              <input
                type="password"
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                placeholder="Enter admin key (stored in this browser)"
              />
            </Field>
            <Field label="Rate limit (requests/min per IP)">
              <input type="number" min="0" max="10000" value={draft.rate_limit_per_minute ?? 60} onChange={(e) => update('rate_limit_per_minute', Number(e.target.value))} />
            </Field>
          </div>

          <div className="keys-section">
            <div className="keys-head">
              <span><Icon name="key" size={15} /> API keys</span>
              <button className="btn tiny" onClick={onCreateKey}><Icon name="key" size={13} /> Generate key</button>
            </div>
            {keys.length === 0 && <p className="aside-muted">No keys yet.</p>}
            {keys.map((k) => (
              <div className="key-row" key={k.key}>
                <code title={k.key}>{k.prefix}••••••••</code>
                <button onClick={() => onCopyKey(k.key)} title="Copy full key"><Icon name="copy" size={14} /></button>
                <button onClick={() => onDeleteKey(k.key)} title="Revoke key"><Icon name="trash" size={14} /></button>
              </div>
            ))}
          </div>
        </section>

        {/* Appearance */}
        <section className="settings-card">
          <div className="card-head"><span className="card-icon tinted"><Icon name="sparkles" size={18} /></span>
            <div><h2>Appearance</h2><p>Make it yours.</p></div>
          </div>
          <div className="card-body form-grid one-col">
            <Field label="Theme">
              <select value={theme} onChange={(e) => setTheme(e.target.value)}>
                <option value="dark">Dark</option>
                <option value="light">Light</option>
              </select>
            </Field>
            <Field label="User agent" hint="Sent to search sources. Some sites block generic bots.">
              <input value={draft.user_agent || ''} onChange={(e) => update('user_agent', e.target.value)} />
            </Field>
          </div>
        </section>
      </div>

      <div className="save-bar">
        <span className={dirty ? 'dirty-label yes' : 'dirty-label'}>
          {dirty ? 'You have unsaved changes' : 'All changes saved'}
        </span>
        <button className="btn primary" onClick={onSave} disabled={saving || !dirty}>
          {saving ? <span className="spinner" /> : <Icon name="check" size={16} />}
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </div>
  )
}
