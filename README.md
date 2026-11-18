# SearNXG

**Free web search for AI models and humans. No search API bill, no vendor lock-in.**

[![Windows](https://img.shields.io/badge/Windows-0078D6?logo=windows&logoColor=white)](README.md#quick-start)
[![macOS](https://img.shields.io/badge/macOS-111827?logo=apple&logoColor=white)](README.md#quick-start)
[![Linux](https://img.shields.io/badge/Linux-FCC624?logo=linux&logoColor=black)](README.md#quick-start)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![MCP compatible](https://img.shields.io/badge/MCP-compatible-7c3aed)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

SearNXG gives an agent **live web results** through one self-hosted backend. Point Claude, Cursor or OpenCode at its **MCP server**, call the **REST API** from a script, or just search in the **browser**. It merges Bing, DuckDuckGo, Wikipedia, Hacker News, GitHub and your own [SearXNG](https://github.com/searxng/searxng) instance into one ranked list, and falls back to a built-in offline library when sources are blocked.

### Why you'll want it

- **Search for your AI, free.** MCP tools (`web_search`, `fetch_url`) work with any MCP client. OpenAI tool schemas included.
- **A UI humans actually like.** Filters, page reader, search history, dark/light themes. No terminal required.
- **Private if you want it.** Run your own SearXNG engine with one Docker command, or use zero-key built-in sources.
- **Hard to break.** Parallel sources, per-source fallbacks, and offline results when the network fights back.
- **One-click setup for agents.** Copy a prompt from the app and let your AI wire up the MCP itself.
- **Runs where you do.** One-command launchers for Windows, macOS and Linux, with a separate environment per OS so switching never breaks your setup. The Linux path is tested on Ubuntu/WSL with Python 3.14.

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
- **Built-in offline library**: if every live source is blocked, search still returns clearly labelled sample results
- **Friendly launchers**: `start.bat` (Windows), `start.sh` / `start.command` (macOS, Linux) check dependencies, install what's missing and pick free ports automatically
- **AI setup prompt**: the MCP docs generate a paste-ready prompt with your live URL and config so an AI harness can add the server itself

---

## Quick start

### Option A — One-command launcher (Windows, macOS, Linux)

| Platform | Run |
| --- | --- |
| Windows | double-click `start.bat` |
| macOS | double-click `start.command`, or `./start.sh` |
| Linux / WSL | `./start.sh` |

The launcher creates a Python environment, installs dependencies, builds the UI, picks free ports automatically, starts both servers and opens your browser. It prints the exact URLs it chose.

If Docker is available it asks whether to also start a local SearXNG engine. Answer **Y** and it runs `docker compose up -d searxng` and connects the app to it; answer **N** and the app uses its built-in sources. Docker is optional on every platform.

On macOS/Linux, run `./stop.sh` to stop both servers. On Windows, close the two terminal windows.

> **Ubuntu/Debian prerequisite:** `sudo apt install python3-venv` (the launcher explains this if it's missing).
> **Port override:** `BACKEND_PORT=8020 UI_PORT=5180 ./start.sh`, or set those variables before running `start.bat`.

### Option B — Manual

Backend (Windows):

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8010
```

Backend (macOS / Linux):

```bash
python3 -m venv .venv-unix
.venv-unix/bin/python -m pip install -r backend/requirements.txt
cd backend
../.venv-unix/bin/python -m uvicorn app.main:app --port 8010
```

Frontend, in a second terminal (any OS):

```bash
cd frontend
npm install
npm run dev
```

Point the dev UI at a non-default API port with `VITE_BACKEND_PORT=8010 VITE_UI_PORT=5174 npm run dev` (macOS/Linux) or `$env:VITE_BACKEND_PORT = 8010; $env:VITE_UI_PORT = 5174; npm run dev` (PowerShell).

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

- Settings → "SearXNG connection" → Instance URL → **Test connection** → Save changes. The app tests the address before saving.
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
