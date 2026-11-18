import React from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { Icon } from './Icons.jsx'

const CATEGORIES = [
  { id: 'general', label: 'All', icon: 'globe' },
  { id: 'web', label: 'Web', icon: 'search' },
  { id: 'news', label: 'News', icon: 'bolt' },
  { id: 'wiki', label: 'Wiki', icon: 'book' },
  { id: 'code', label: 'Code', icon: 'code' },
  { id: 'discussions', label: 'Discuss', icon: 'message' },
]

const LANGUAGES = [
  ['en', 'English'], ['es', 'Español'], ['fr', 'Français'], ['de', 'Deutsch'],
  ['it', 'Italiano'], ['pt', 'Português'], ['ja', '日本語'], ['zh', '中文'], ['ru', 'Русский'],
]

const EXAMPLES = [
  'What is Model Context Protocol?',
  'latest AI news this week',
  'python async best practices',
  'github: fastapi alternatives',
]

function domainOf(url) {
  try { return new URL(url).hostname.replace(/^www\./, '') } catch { return url }
}

function Highlight({ text, query }) {
  const terms = (query || '').split(/\s+/).map((t) => t.replace(/[^\p{L}\p{N}]/gu, '')).filter((t) => t.length > 2)
  if (!terms.length) return text
  const escaped = terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const parts = String(text).split(new RegExp(`(${escaped.join('|')})`, 'gi'))
  return parts.map((part, i) =>
    terms.some((t) => t.toLowerCase() === part.toLowerCase()) ? <mark key={i}>{part}</mark> : part,
  )
}

function SearchForm({ query, setQuery, onSubmit, loading, big }) {
  return (
    <form
      className={`search-form ${big ? 'big' : ''}`}
      onSubmit={(e) => { e.preventDefault(); onSubmit() }}
    >
      <Icon name="search" size={big ? 20 : 17} className="search-form-icon" />
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search the web, ask a question, find a repo..."
        aria-label="Search query"
        autoComplete="off"
        autoFocus={big}
      />
      {query && (
        <button type="button" className="search-clear" onClick={() => setQuery('')} aria-label="Clear search">
          <Icon name="close" size={15} />
        </button>
      )}
      <button type="submit" className="search-submit" disabled={loading || !query.trim()}>
        {loading ? <span className="spinner" /> : <Icon name="arrow" size={17} />}
        <span>{loading ? 'Searching' : 'Search'}</span>
      </button>
    </form>
  )
}

function Skeletons() {
  return (
    <div className="skeleton-list" aria-label="Loading results" aria-busy="true">
      {[0, 1, 2, 3].map((i) => (
        <div className="skeleton-card" key={i}>
          <div className="skeleton-line w20" />
          <div className="skeleton-line w55" />
          <div className="skeleton-line w80" />
          <div className="skeleton-line w55" />
        </div>
      ))}
    </div>
  )
}

export default function SearchView({
  query, setQuery, filters, onFilterChange, response, loading, error,
  onSearch, onRead, onCopyJson, onCopyMd, onSetView, history,
  onHistoryClick, onHistoryRemove, config, setup, onOpenSetup,
}) {
  const reduce = useReducedMotion()
  const hasResults = response && response.results.length > 0
  const isHome = !response && !loading && !error
  const limitOptions = [5, 10, 20, 50].filter((n) => n <= (config?.max_limit || 50))
  const enter = reduce ? {} : { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 } }

  if (isHome) {
    return (
      <div className="home">
        {setup?.needs_setup && (
          <motion.div className="setup-banner" {...enter} transition={{ duration: 0.4 }}>
            <span className="setup-banner-icon"><Icon name="sparkles" size={17} /></span>
            <div className="setup-banner-copy">
              <strong>New here? Let's get you set up.</strong>
              <span>About a minute. No technical knowledge needed.</span>
            </div>
            <button className="btn primary" onClick={onOpenSetup}>Set up <Icon name="arrow" size={15} /></button>
          </motion.div>
        )}
        <section className="hero">
          <motion.div className="hero-copy" {...enter} transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}>
            <span className="eyebrow"><Icon name="sparkles" size={13} /> Web search for humans &amp; models</span>
            <h1>Find what you need.<br /><em>Fuel what you build.</em></h1>
            <p className="hero-sub">
              One search layer for the browser and for any AI model. REST, MCP, and OpenAI tools included.
            </p>
            <SearchForm query={query} setQuery={setQuery} onSubmit={onSearch} loading={loading} big />
            <div className="examples">
              <span>Try</span>
              {EXAMPLES.map((ex) => (
                <button key={ex} onClick={() => { setQuery(ex); onSearch(ex) }}>{ex}</button>
              ))}
            </div>
          </motion.div>

          <motion.div
            className="hero-terminal"
            {...enter}
            transition={{ duration: 0.55, delay: reduce ? 0 : 0.08, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="terminal-head"><i /><i /><i /><span>searnxg / api</span></div>
            <pre><code>
              <span className="tk">POST</span> /api/search{'\n'}
              {'{ '}<span className="tm">"query"</span>: <span className="tm">"what is MCP"</span>, <span className="tm">"limit"</span>: 5 {'}'}{'\n\n'}
              <span className="tm">// example response</span>{'\n'}
              → <span className="tk">8</span> results · <span className="tk">3</span> sources · <span className="tk">412ms</span>
            </code></pre>
            <div className="terminal-foot"><Icon name="pulse" size={14} /> REST · MCP · OpenAI tools</div>
          </motion.div>
        </section>

        <section className="feature-row">
          <motion.div className="feature-card" {...enter} transition={{ duration: 0.5, delay: reduce ? 0 : 0.12 }}>
            <span className="feature-icon"><Icon name="stack" size={19} /></span>
            <div>
              <h3>Every source, one answer</h3>
              <p>Bing, Wikipedia, Hacker News, GitHub, DuckDuckGo and your own SearXNG instance, merged and ranked in parallel.</p>
            </div>
            <div className="feature-code">
              <b>POST /api/search</b>{'\n'}
              <b>MCP</b> web_search, fetch_url{'\n'}
              <b>UI</b> filters, reader, history
            </div>
          </motion.div>
          <div className="feature-card">
            <span className="feature-icon tinted"><Icon name="code" size={19} /></span>
            <h3>Built for agents</h3>
            <p>Call it from an MCP client, an OpenAI tool loop, or a one-line curl request. Same results everywhere.</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon tinted"><Icon name="shield" size={19} /></span>
            <h3>Yours to control</h3>
            <p>Toggle sources, add keys, set limits and connect your own SearXNG. Changes persist to disk.</p>
          </div>
        </section>
      </div>
    )
  }

  const listVariants = {
    hidden: {},
    show: { transition: { staggerChildren: reduce ? 0 : 0.035 } },
  }
  const itemVariants = {
    hidden: reduce ? {} : { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] } },
  }

  return (
    <div className="results-layout">
      <main className="results-main">
        <SearchForm query={query} setQuery={setQuery} onSubmit={onSearch} loading={loading} />

        <div className="filter-bar">
          <div className="category-tabs">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                className={`category-tab ${filters.category === cat.id ? 'active' : ''}`}
                onClick={() => onFilterChange({ category: cat.id })}
              >
                <Icon name={cat.icon} size={13} />
                {cat.label}
              </button>
            ))}
          </div>
          <div className="filter-controls">
            <select value={filters.language} onChange={(e) => onFilterChange({ language: e.target.value })} aria-label="Language">
              {LANGUAGES.map(([code, label]) => <option key={code} value={code}>{label}</option>)}
            </select>
            <select value={filters.time_range} onChange={(e) => onFilterChange({ time_range: e.target.value })} aria-label="Time range">
              <option value="">Any time</option>
              <option value="day">Past day</option>
              <option value="week">Past week</option>
              <option value="month">Past month</option>
              <option value="year">Past year</option>
            </select>
            <select value={filters.limit} onChange={(e) => onFilterChange({ limit: Number(e.target.value) })} aria-label="Results per page">
              {limitOptions.map((n) => <option key={n} value={n}>{n} results</option>)}
            </select>
            <label className="safe-toggle" title="Filter explicit content where supported">
              <input type="checkbox" checked={filters.safesearch} onChange={(e) => onFilterChange({ safesearch: e.target.checked })} />
              Safe
            </label>
          </div>
        </div>

        {error && (
          <div className="error-box">
            <Icon name="info" size={17} />
            <div><strong>Search failed</strong><p>{error}</p></div>
          </div>
        )}

        {response && (
          <div className="results-meta">
            <span>
              <strong>{response.number_of_results}</strong> results for <strong>“{response.query}”</strong>
              {' · '}{response.took_ms} ms{response.cached && ' · cached'}
            </span>
            <div className="source-chips">
              {response.providers.filter((p) => p.ok).map((p) => (
                <span key={p.provider} className="source-chip ok" title={`${p.results} results in ${p.duration_ms} ms`}>
                  <span className="mini-dot" />{p.provider} <em>{p.results}</em>
                </span>
              ))}
              {response.providers.filter((p) => !p.ok).map((p) => (
                <span key={p.provider} className="source-chip bad" title={p.error || 'unavailable'}>
                  <span className="mini-dot bad" />{p.provider}
                </span>
              ))}
            </div>
          </div>
        )}

        {loading && !response && <Skeletons />}

        {hasResults && (
          <motion.div className="result-list" variants={listVariants} initial="hidden" animate="show" key={response.query + filters.category}>
            {response.results.map((r, i) => (
              <motion.article className="result-card" key={`${r.url}-${i}`} variants={itemVariants}>
                <div className="result-top">
                  {r.favicon && <img src={r.favicon} alt="" className="favicon" onError={(e) => { e.currentTarget.style.display = 'none' }} />}
                  <span className="result-domain">{domainOf(r.url)}</span>
                  <span className="engine-badge">{r.engine}</span>
                  {r.published_date && <span className="result-date">{r.published_date}</span>}
                </div>
                <a className="result-title" href={r.url} target="_blank" rel="noreferrer">
                  <Highlight text={r.title} query={response.query} />
                  <Icon name="external" size={13} />
                </a>
                <p className="result-snippet"><Highlight text={r.content} query={response.query} /></p>
                <div className="result-actions">
                  {config?.extract_enabled && (
                    <button onClick={() => onRead(r.url)}><Icon name="bookOpen" size={13} /> Read page</button>
                  )}
                  <button onClick={() => navigator.clipboard?.writeText(r.url)}><Icon name="copy" size={13} /> Copy link</button>
                </div>
              </motion.article>
            ))}
          </motion.div>
        )}

        {response && !hasResults && !loading && !error && (
          <div className="empty-state">
            <Icon name="search" size={26} />
            <h3>No results found</h3>
            <p>Try another query, enable more sources in Settings, or connect your own SearXNG instance.</p>
          </div>
        )}
      </main>

      <aside className="results-aside">
        <div className="aside-card">
          <div className="aside-title"><Icon name="bolt" size={14} /> Quick actions</div>
          <button className="aside-action" onClick={onCopyJson}><Icon name="copy" size={14} /> Copy results as JSON</button>
          <button className="aside-action" onClick={onCopyMd}><Icon name="copy" size={14} /> Copy as Markdown</button>
          <button className="aside-action" onClick={() => onSetView('docs')}><Icon name="code" size={14} /> API &amp; MCP docs</button>
        </div>

        <div className="aside-card">
          <div className="aside-title"><Icon name="database" size={14} /> Source status</div>
          {response ? response.providers.map((p) => (
            <div className="source-row" key={p.provider} title={p.error || ''}>
              <span className={`mini-dot ${p.ok ? 'ok' : 'bad'}`} />
              <span className="source-name">{p.provider}</span>
              <span className="source-stat">{p.ok ? `${p.results} · ${p.duration_ms}ms` : 'offline'}</span>
            </div>
          )) : <p className="aside-muted">Run a search to see source status.</p>}
        </div>

        <div className="aside-card">
          <div className="aside-title"><Icon name="history" size={14} /> Recent searches</div>
          {history.length === 0 && <p className="aside-muted">Your search history appears here.</p>}
          {history.map((item) => (
            <div className="history-row" key={`${item.q}-${item.ts}`}>
              <button onClick={() => onHistoryClick(item.q)}>
                <Icon name="history" size={12} />
                <span>{item.q}</span>
              </button>
              <button className="history-delete" onClick={() => onHistoryRemove(item.ts)} aria-label="Remove from history">
                <Icon name="close" size={12} />
              </button>
            </div>
          ))}
        </div>
      </aside>
    </div>
  )
}
