# SearNXG

A self-hosted web search layer for **humans and AI models**.

SearNXG aggregates multiple no-key search sources (Bing, DuckDuckGo, Wikipedia, Hacker News, GitHub) and your own [SearXNG](https://github.com/searxng/searxng) instance into one clean result set, then exposes it three ways:

1. **A polished web UI** for people — search, filters, page reader, history, settings.
2. **A REST API** for scripts and agents — JSON, Markdown or plain-text results.
3. **An MCP server** with `web_search`, `fetch_url` and `list_sources` tools for Claude, Cursor and other AI clients.

---

## Features

- Multi-source parallel search with per-source status, deduplication and ranking
- Categories: `general`, `web`, `news`, `wiki`, `code`, `discussions`
- Filters: language, time range, safe search, result count, pagination
- Page extraction (`fetch_url`) — readable Markdown from any result
- Runtime settings UI: toggle providers, configure SearXNG URL/API key, themes, timeouts, cache, rate limits
- API key management and optional API-key protection for machine endpoints
- MCP over **SSE** (`/mcp/sse`) and **Streamable HTTP** (`/mcp-http/mcp`)
- Ready-to-paste OpenAI function-calling tool definitions at `/api/tools/openai`
- Dark/light theme, keyboard shortcut `/`, search history, copy-as-JSON/Markdown
- **First-run setup wizard** with plain-language choices, opened automatically on a fresh install
- **Simple / Advanced settings**: non-technical users see everyday controls by default; power users can switch
- **Built-in offline library**: if every live source is blocked, search still returns clearly labelled sample results
- **Friendly launcher**: `start.bat` checks for Python/Node, installs what's missing and picks free ports automatically

---

## Quick start

### Option A — Local (Windows)

```bat
start.bat
```

The script creates a Python venv, installs backend and frontend dependencies, builds the UI, and starts both servers. It picks free ports automatically, so it prints the exact URLs it chose.

If Docker is installed and running, the script asks whether to also start a local SearXNG engine. Answer **Y** and it runs `docker compose up -d searxng` and connects the app to it; answer **N** and the app uses its built-in sources. Docker is entirely optional.

Open the printed UI URL (for example `http://localhost:5174`) in your browser.

> **Port conflicts:** if 8000 or 5173 are already used by another app, pick free ports.
> `uvicorn app.main:app --port 8010` for the API, then in the frontend:
> `$env:VITE_BACKEND_PORT = 8010; $env:VITE_UI_PORT = 5174; npm run dev`.

### Option B — Manual

```bash
# Backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Option C — Docker (includes a real SearXNG instance)

```bash
npm --prefix frontend install
npm --prefix frontend run build
docker compose up --build
```

- App + API + UI: http://localhost:8000
- Bundled SearXNG: http://localhost:8080

The bundled SearXNG is preconfigured to expose JSON results; SearNXG connects to it automatically via the Compose environment.

---

## About SearXNG instances

**You do not need one.** SearNXG already searches Bing, DuckDuckGo, Wikipedia, Hacker News and GitHub. A SearXNG instance is an optional extra metasearch engine you run yourself.

Where does the address come from?

1. **Run your own (recommended).** With Docker installed, run `docker compose up` in this folder. The Compose file starts a SearXNG instance on **http://localhost:8080** and passes that address to the app automatically. Nothing to paste.
2. **You already run one.** Use its address, e.g. `http://localhost:8080` or `https://searx.example.com`.
3. **Public instances.** Lists like [searx.space](https://searx.space/) exist, but many disable the JSON API or block automated requests, so they are less reliable. Self-hosting is better.

How to connect:

- **Simple view:** Settings → "Your own search engine (optional)" → paste the address → **Connect**. It tests the address before saving.
- **Advanced view:** Settings → "SearXNG connection" → Instance URL → **Test connection** → Save changes.
- **Environment variable:** `SEARXNG_URL=http://localhost:8080` overrides the saved value at startup.
- **Docker Compose:** already wired for you via `SEARXNG_URL: http://searxng:8080`.

SearXNG must expose JSON results for the best integration. The bundled `searxng/settings.yml` enables this. If JSON is disabled, SearNXG's `auto` mode falls back to reading the HTML results page instead.

## Using the API

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"query":"what is MCP","category":"general","limit":5}'
```

Query-string form:

```
GET /api/search?q=python+async&limit=5&format=markdown
```

Other endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Status, version, MCP flag |
| `GET` | `/api/config` | Public config (safe for clients) |
| `POST` | `/api/ui/search` | UI endpoint (rate limited, no API key) |
| `POST` | `/api/extract` | Fetch a URL → readable Markdown |
| `GET` | `/api/tools/openai` | OpenAI tool definitions |
| `GET` | `/api/tools/mcp` | MCP client config snippets |
| `GET` | `/api/settings` / `PUT` | Runtime settings (admin key) |
| `GET` | `/api/docs` | Interactive OpenAPI docs |

Enable **Require API key** in Settings to protect `/api/search` and `/api/extract`. Keys are managed in Settings → API & security, or via environment variables.

---

## Connecting AI models

### MCP (recommended)

Add to your MCP client config:

```json
{
  "mcpServers": {
    "searnxg": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8000/mcp/sse"]
    }
  }
}
```

Streamable HTTP is also available at `http://localhost:8000/mcp-http/mcp`.

Tools:

- `web_search(query, limit, category, language, time_range)` → ranked Markdown results
- `fetch_url(url, max_chars)` → readable page content
- `list_sources()` → enabled providers

### OpenAI function calling

Fetch `/api/tools/openai` and pass the returned array as the `tools` parameter. When the model emits a tool call, map `web_search` → `POST /api/search` and `fetch_url` → `POST /api/extract`.

---

## Configuration

Settings are stored in `backend/data/settings.json` and can be edited in the UI or overridden with environment variables (see `backend/.env.example`):

| Variable | Meaning |
| --- | --- |
| `SEARXNG_URL` | Your SearXNG instance URL (auto-enables the provider) |
| `SEARXNG_API_KEY` | Optional key sent to SearXNG |
| `API_KEYS` | Comma-separated accepted API keys |
| `ADMIN_KEY` | Protects settings & key-management endpoints |
| `REQUIRE_API_KEY` | `true` to protect machine endpoints |
| `DEFAULT_LIMIT` / `TIMEOUT` | Search defaults |

> **Note on sources:** public search engines and Wikipedia enforce their own bot policies. Some cloud/datacenter IPs may be blocked by DuckDuckGo or Wikimedia. The app runs all enabled providers in parallel and reports each one's status, so a single blocked source never breaks search. Pointing SearNXG at your own SearXNG instance is the most reliable setup.

---

## Project layout

```
searnxg/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, REST endpoints, static UI host
│   │   ├── config.py        # persistent settings
│   │   ├── search.py        # orchestration, ranking, cache
│   │   ├── extract.py       # trafilatura page extraction
│   │   ├── mcp_server.py    # MCP tools
│   │   └── providers/       # bing, duckduckgo, wikipedia, hackernews, github, searxng
│   └── requirements.txt
├── frontend/
│   └── src/                 # React UI (search, settings, docs, reader)
├── searxng/settings.yml     # JSON-enabled SearXNG config for Docker
├── Dockerfile
├── docker-compose.yml
└── start.bat
```

MIT licensed. Built for people who want search they can own.
