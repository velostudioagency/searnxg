import React, { useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { api, API_BASE } from './api.js'
import Header from './components/Header.jsx'
import SearchView from './components/SearchView.jsx'
import SettingsPanel from './components/SettingsPanel.jsx'
import DocsPanel from './components/DocsPanel.jsx'
import ReaderModal from './components/ReaderModal.jsx'
import SetupWizard from './components/SetupWizard.jsx'
import Toast from './components/Toast.jsx'

const DEFAULT_FILTERS = {
  category: 'general',
  limit: 10,
  language: 'en',
  safesearch: false,
  time_range: '',
}

function loadLocal(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

export default function App() {
  const [view, setViewState] = useState('search')
  const [theme, setThemeState] = useState(() => localStorage.getItem('searnxg.theme') || 'dark')
  const [online, setOnline] = useState(false)
  const [config, setConfig] = useState(null)
  const [setup, setSetup] = useState(null)
  const [showSetup, setShowSetup] = useState(false)
  const [mcpConfig, setMcpConfig] = useState(null)
  const [openaiTools, setOpenaiTools] = useState(null)

  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [history, setHistory] = useState(() => loadLocal('searnxg.history', []))
  const [readerUrl, setReaderUrl] = useState(null)
  const [toast, setToast] = useState(null)

  const [settings, setSettings] = useState(null)
  const [draft, setDraft] = useState(null)
  const [keys, setKeys] = useState([])
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [adminKey, setAdminKeyState] = useState(() => localStorage.getItem('searnxg.adminKey') || '')

  const searchSeq = useRef(0)
  const toastTimer = useRef(null)
  const reduceMotion = useReducedMotion()

  const dirty = useMemo(
    () => Boolean(settings && draft && JSON.stringify(settings) !== JSON.stringify(draft)),
    [settings, draft],
  )

  function showToast(message, type = 'success') {
    setToast({ message, type })
    clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3500)
  }

  async function copy(text, message = 'Copied to clipboard') {
    try {
      await navigator.clipboard.writeText(text)
      showToast(message)
    } catch {
      showToast('Clipboard access is blocked by this browser', 'error')
    }
  }

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('searnxg.theme', theme)
  }, [theme])

  useEffect(() => {
    let active = true
    async function init() {
      try {
        const [health, cfg, setupStatus] = await Promise.all([api.health(), api.config(), api.setup()])
        if (!active) return
        setOnline(health.status === 'ok')
        setConfig(cfg)
        setSetup(setupStatus)
        if (setupStatus.needs_setup) setShowSetup(true)
        if (cfg.mcp_enabled) api.mcpConfig().then((d) => active && setMcpConfig(d)).catch(() => {})
        api.openaiTools().then((d) => active && setOpenaiTools(d)).catch(() => {})
      } catch {
        if (active) setOnline(false)
      }
    }
    init()
    const timer = setInterval(() => {
      api.health().then((h) => active && setOnline(h.status === 'ok')).catch(() => active && setOnline(false))
    }, 30000)
    return () => { active = false; clearInterval(timer) }
  }, [])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === '/' && view === 'search') {
        const tag = document.activeElement?.tagName
        if (tag !== 'INPUT' && tag !== 'TEXTAREA' && tag !== 'SELECT') {
          e.preventDefault()
          document.querySelector('input[aria-label="Search query"]')?.focus()
        }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [view])

  async function runSearch(q = query, f = filters) {
    const term = String(q || '').trim()
    if (!term) return
    const seq = ++searchSeq.current
    setQuery(term)
    setSubmittedQuery(term)
    setLoading(true)
    setError('')
    try {
      const result = await api.search({
        query: term,
        category: f.category,
        limit: f.limit,
        language: f.language,
        safesearch: f.safesearch,
        time_range: f.time_range,
      })
      if (seq !== searchSeq.current) return
      setResponse(result)
      setHistory((prev) => {
        const next = [{ q: term, ts: Date.now() }, ...prev.filter((h) => h.q !== term)].slice(0, 15)
        localStorage.setItem('searnxg.history', JSON.stringify(next))
        return next
      })
    } catch (err) {
      if (seq !== searchSeq.current) return
      setError(err.message || 'Search failed')
      setResponse(null)
    } finally {
      if (seq === searchSeq.current) setLoading(false)
    }
  }

  function onFilterChange(patch) {
    const next = { ...filters, ...patch }
    setFilters(next)
    if (submittedQuery && !loading) runSearch(submittedQuery, next)
  }

  function setView(next) {
    setViewState(next)
    if (next === 'settings' && !settings) loadSettings()
    if (next === 'docs') {
      if (!mcpConfig) api.mcpConfig().then(setMcpConfig).catch(() => {})
      if (!openaiTools) api.openaiTools().then(setOpenaiTools).catch(() => {})
    }
  }

  async function loadSettings() {
    try {
      const result = await api.getSettings()
      setSettings(result.settings)
      setDraft(structuredClone(result.settings))
      const keyList = await api.listKeys()
      setKeys(keyList)
    } catch (err) {
      showToast(err.message || 'Could not load settings', 'error')
    }
  }

  async function saveSettings() {
    setSaving(true)
    try {
      const result = await api.updateSettings(draft)
      setSettings(result.settings)
      setDraft(structuredClone(result.settings))
      setConfig(result.public)
      setKeys(await api.listKeys())
      api.setup().then(setSetup).catch(() => {})
      showToast('Settings saved')
    } catch (err) {
      showToast(err.message || 'Could not save settings', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function testConnection() {
    setTesting(true)
    setTestResult(null)
    try {
      const result = await api.testSearxng(draft.searxng_url, draft.searxng_format)
      setTestResult(result)
      showToast(result.ok ? 'Connection successful' : 'Connection failed', result.ok ? 'success' : 'error')
    } catch (err) {
      setTestResult({ ok: false, message: err.message })
    } finally {
      setTesting(false)
    }
  }

  async function createKey() {
    try {
      const result = await api.createKey()
      setKeys(await api.listKeys())
      copy(result.key, 'New key copied to clipboard')
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  async function deleteKey(key) {
    try {
      await api.deleteKey(key)
      setKeys(await api.listKeys())
      showToast('Key revoked')
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  function setTheme(next) {
    setThemeState(next)
    if (draft) setDraft((prev) => ({ ...prev, theme: next }))
  }

  function setAdminKey(value) {
    setAdminKeyState(value)
    localStorage.setItem('searnxg.adminKey', value)
  }

  function completeSetup(publicCfg) {
    if (publicCfg) setConfig(publicCfg)
    api.setup().then(setSetup).catch(() => {})
    showToast('You are all set')
  }

  return (
    <div className="app">
      <Header
        view={view}
        setView={setView}
        theme={theme}
        onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        online={online}
      />

      <div className={`content ${view}`}>
        <motion.div
          key={view}
          initial={reduceMotion ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.26, ease: [0.16, 1, 0.3, 1] }}
        >
        {view === 'search' && (
          <SearchView
            query={query}
            setQuery={setQuery}
            filters={filters}
            onFilterChange={onFilterChange}
            response={response}
            loading={loading}
            error={error}
            onSearch={(q) => runSearch(q ?? query)}
            onRead={setReaderUrl}
            onCopyJson={() => response && copy(JSON.stringify(response, null, 2), 'Results JSON copied')}
            onCopyMd={() => {
              if (!response) return
              const md = response.results
                .map((r, i) => `${i + 1}. **[${r.title}](${r.url})** · ${r.engine}\n   ${r.content}`)
                .join('\n\n')
              copy(`## ${response.query}\n\n${md}`, 'Markdown copied')
            }}
            onSetView={setView}
            history={history}
            onHistoryClick={(q) => { setQuery(q); runSearch(q) }}
            onHistoryRemove={(ts) => {
              const next = history.filter((h) => h.ts !== ts)
              setHistory(next)
              localStorage.setItem('searnxg.history', JSON.stringify(next))
            }}
            config={config}
            setup={setup}
            onOpenSetup={() => setShowSetup(true)}
          />
        )}

        {view === 'docs' && (
          <DocsPanel
            apiBase={API_BASE}
            config={config}
            mcpConfig={mcpConfig}
            openaiTools={openaiTools}
            onCopy={(text) => copy(text, 'Snippet copied')}
          />
        )}

        {view === 'settings' && (
          draft ? (
            <SettingsPanel
              draft={draft}
              setDraft={setDraft}
              onSave={saveSettings}
              saving={saving}
              dirty={dirty}
              onTest={testConnection}
              testing={testing}
              testResult={testResult}
              keys={keys}
              onCreateKey={createKey}
              onDeleteKey={deleteKey}
              onCopyKey={(k) => copy(k, 'API key copied')}
              adminKey={adminKey}
              setAdminKey={setAdminKey}
              config={config}
              theme={theme}
              setTheme={setTheme}
            />
          ) : (
            <div className="loading-state"><span className="spinner big-spinner" /><p>Loading settings…</p></div>
          )
        )}
        </motion.div>
      </div>

      <footer className="footer">
        <span>SearNXG · web search for humans &amp; models</span>
        <span>
          <a href="/api/docs" target="_blank" rel="noreferrer">OpenAPI</a>
          {' · '}
          <kbd>/</kbd> to search
        </span>
      </footer>

      <AnimatePresence>
        {readerUrl && (
          <ReaderModal url={readerUrl} onClose={() => setReaderUrl(null)} onCopy={(text) => copy(text, 'Page text copied')} />
        )}
      </AnimatePresence>
      <AnimatePresence>
        <Toast toast={toast} onClose={() => setToast(null)} />
      </AnimatePresence>
      <AnimatePresence>
        {showSetup && (
          <SetupWizard
            setup={setup}
            onClose={() => setShowSetup(false)}
            onComplete={completeSetup}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
