import React, { useState } from 'react'
import { Icon } from './Icons.jsx'

function CodeBlock({ code, label, onCopy }) {
  return (
    <div className="code-block">
      <div className="code-head">
        <span>{label}</span>
        <button onClick={() => onCopy(code)}><Icon name="copy" size={13} /> Copy</button>
      </div>
      <pre><code>{code}</code></pre>
    </div>
  )
}

const ENDPOINTS = [
  ['GET', '/api/health', 'Health check, version and provider status'],
  ['GET', '/api/config', 'Public configuration for clients'],
  ['POST', '/api/search', 'Search the web (JSON / Markdown / text)'],
  ['GET', '/api/search?q=...', 'Search via query string'],
  ['POST', '/api/extract', 'Fetch and read a page as Markdown'],
  ['GET', '/api/tools/openai', 'Ready-to-use OpenAI tool definitions'],
  ['GET', '/api/tools/mcp', 'MCP client configuration'],
  ['GET', '/api/docs', 'Interactive OpenAPI documentation'],
]

export default function DocsPanel({ apiBase, config, mcpConfig, openaiTools, onCopy }) {
  const [tab, setTab] = useState('rest')
  const base = apiBase || 'http://localhost:8000'

  const curl = `curl -X POST ${base}/api/search \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{"query":"what is MCP","category":"general","limit":5}'`

  const python = `import requests

response = requests.post(
    "${base}/api/search",
    json={"query": "latest AI news", "category": "news", "limit": 5},
    headers={"X-API-Key": "YOUR_API_KEY"},
)
for r in response.json()["results"]:
    print(r["title"], "→", r["url"])`

  const javascript = `const res = await fetch("${base}/api/search", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": "YOUR_API_KEY",
  },
  body: JSON.stringify({ query: "python async", limit: 5 }),
});
const { results } = await res.json();`

  const streamUrl = `${base}/mcp-http/mcp`
  const sseUrl = `${base}/mcp/sse`

  const opencodeConfig = JSON.stringify({
    $schema: 'https://opencode.ai/config.json',
    mcp: {
      servers: {
        searnxg: { type: 'remote', url: streamUrl, oauth: false },
      },
    },
  }, null, 2)

  const genericConfig = JSON.stringify({
    mcpServers: {
      searnxg: { command: 'npx', args: ['-y', 'mcp-remote', sseUrl] },
    },
  }, null, 2)

  const aiPrompt = [
    'Add the SearNXG web-search MCP server to this harness.',
    '',
    'Server name: searnxg',
    'Transport: Streamable HTTP',
    `URL: ${streamUrl}`,
    'Authentication: none. If your client enables OAuth by default, disable it.',
    '',
    `For OpenCode, add this to opencode.json (or run: opencode mcp add searnxg --global --url ${streamUrl}, then set oauth to false):`,
    opencodeConfig,
    '',
    'Expected tools: web_search, fetch_url, list_sources.',
    'After adding, run "opencode mcp list" and confirm searnxg shows as connected. If it says "needs authentication", set "oauth": false in the config.',
    '',
    `Keep SearNXG running at ${base}; the MCP endpoint must stay reachable.`,
  ].join('\n')

  const openaiJson = JSON.stringify(openaiTools || [], null, 2)

  const openaiSnippet = `from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    tools=${JSON.stringify(openaiTools?.slice(0, 1) || [], null, 2).replace(/\n/g, '\n  ')},
    messages=[{"role": "user", "content": "What happened in AI this week?"}],
)`

  return (
    <div className="docs-page">
      <div className="page-heading">
        <div>
          <h1>API &amp; MCP</h1>
          <p>Everything you need to call SearNXG from an AI model, agent, or your own app.</p>
        </div>
        <span className="version-badge">v{config?.version || '1.0.0'}</span>
      </div>

      <div className="doc-tabs">
        {[
          ['rest', 'REST API'],
          ['mcp', 'MCP server'],
          ['openai', 'OpenAI tools'],
        ].map(([id, label]) => (
          <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>

      {tab === 'rest' && (
        <div className="doc-content">
          <section className="doc-section">
            <h2>Search endpoint</h2>
            <p><code>POST /api/search</code> accepts a JSON body. Results are merged from all enabled sources, deduplicated and ranked.</p>
            <div className="param-grid">
              <div><code>query</code><span>Required. Search text (1–500 chars).</span></div>
              <div><code>category</code><span>general · web · news · wiki · code · discussions</span></div>
              <div><code>limit</code><span>Number of results (1–{config?.max_limit || 50}).</span></div>
              <div><code>page</code><span>Page number, starting at 1.</span></div>
              <div><code>language</code><span>Language code, e.g. <code>en</code>.</span></div>
              <div><code>time_range</code><span>day · week · month · year</span></div>
              <div><code>safesearch</code><span>Boolean.</span></div>
              <div><code>format</code><span>json · markdown · text</span></div>
            </div>
          </section>

          <section className="doc-section">
            <h2>Quick start</h2>
            <CodeBlock label="cURL" code={curl} onCopy={onCopy} />
            <div className="code-row">
              <CodeBlock label="Python" code={python} onCopy={onCopy} />
              <CodeBlock label="JavaScript" code={javascript} onCopy={onCopy} />
            </div>
          </section>

          <section className="doc-section">
            <h2>Endpoints</h2>
            <div className="endpoint-table">
              {ENDPOINTS.map(([method, path, desc]) => (
                <div className="endpoint-row" key={path}>
                  <span className={`method ${method.toLowerCase()}`}>{method}</span>
                  <code>{path}</code>
                  <span>{desc}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="doc-section callout">
            <Icon name="info" size={18} />
            <p>When <strong>Require API key</strong> is enabled in Settings, pass your key as <code>Authorization: Bearer &lt;key&gt;</code> or <code>X-API-Key: &lt;key&gt;</code>. The web UI uses a separate rate-limited endpoint and keeps working.</p>
          </section>
        </div>
      )}

      {tab === 'mcp' && (
        <div className="doc-content">
          <section className="doc-section callout">
            <Icon name="sparkles" size={18} />
            <div className="callout-main">
              <h2 style={{ marginBottom: 6 }}>Let your AI add it</h2>
              <p style={{ marginBottom: 12 }}>Copy this prompt into your AI harness. It contains the live URL and the exact config, so the model can wire up the server for you.</p>
              <CodeBlock label="Prompt to paste into your AI" code={aiPrompt} onCopy={onCopy} />
            </div>
          </section>

          <section className="doc-section">
            <h2>Connect an MCP client</h2>
            <p>SearNXG ships an MCP server with three tools. Add it to OpenCode, Claude Desktop, Cursor, or any MCP-compatible agent.</p>
            <div className="code-row">
              <CodeBlock label="OpenCode config" code={opencodeConfig} onCopy={onCopy} />
              <CodeBlock label="Other clients (mcp-remote)" code={genericConfig} onCopy={onCopy} />
            </div>
            <div className="tool-list" style={{ marginTop: 12 }}>
              <div><code>web_search</code><span>Search the live web; returns ranked Markdown results.</span></div>
              <div><code>fetch_url</code><span>Read a page and return clean Markdown.</span></div>
              <div><code>list_sources</code><span>Show enabled search providers.</span></div>
            </div>
          </section>
          <section className="doc-section">
            <h2>Endpoints</h2>
            <div className="endpoint-table">
              <div className="endpoint-row"><span className="method get">SSE</span><code>{base}/mcp/sse</code><span>Legacy SSE transport.</span></div>
              <div className="endpoint-row"><span className="method post">HTTP</span><code>{base}/mcp-http/mcp</code><span>Streamable HTTP transport.</span></div>
            </div>
            <p className="muted">Status: {mcpConfig?.enabled ? 'enabled' : 'disabled in settings'}</p>
          </section>
        </div>
      )}

      {tab === 'openai' && (
        <div className="doc-content">
          <section className="doc-section">
            <h2>Function calling schema</h2>
            <p>Paste these tool definitions into the <code>tools</code> parameter of the OpenAI Chat Completions API. When the model calls a tool, execute it against the corresponding SearNXG endpoint.</p>
            <CodeBlock label="tools.json" code={openaiJson} onCopy={onCopy} />
          </section>
          <section className="doc-section">
            <h2>Example</h2>
            <CodeBlock label="Python (OpenAI SDK)" code={openaiSnippet} onCopy={onCopy} />
          </section>
        </div>
      )}
    </div>
  )
}
