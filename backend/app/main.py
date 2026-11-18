"""SearNXG FastAPI application — REST API, MCP server and web UI host."""

from __future__ import annotations

import json
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .auth import require_admin, require_api_key
from .config import (
    BASE_DIR,
    PROVIDER_LABELS,
    get_settings,
    is_first_run,
    load_settings,
    public_config,
    set_settings,
    update_settings,
)
from .extract import extract_url
from .models import (
    CreateKeyRequest,
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    SearchRequest,
    SettingsPatch,
    TestConnectionResponse,
)
from .search import _cache, execute_search, format_results

START_TIME = time.time()
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

_client: httpx.AsyncClient | None = None
_mcp_server = None
_mcp_http_app = None

_initial = load_settings()
set_settings(_initial)


def get_client() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("HTTP client is not ready")
    return _client


@asynccontextmanager
async def _mcp_lifespan():
    """Mounted Starlette apps don't get their lifespan run automatically."""
    if _mcp_http_app is not None:
        async with _mcp_http_app.router.lifespan_context(_mcp_http_app):
            yield
    else:
        yield


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    settings = load_settings()
    set_settings(settings)
    _client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.timeout, connect=10.0),
        follow_redirects=True,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=30),
    )
    async with _mcp_lifespan():
        try:
            yield
        finally:
            await _client.aclose()
            _client = None


app = FastAPI(
    title="SearNXG API",
    description=(
        "Web search for humans and AI models. REST API, MCP tools, and a clean web UI. "
        "Search results are aggregated from configurable providers."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_initial.cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# MCP server (optional dependency / version tolerant)
# ---------------------------------------------------------------------------
try:
    from .mcp_server import create_mcp_server

    _mcp_server = create_mcp_server(get_client, get_settings)
    try:
        app.mount("/mcp", _mcp_server.sse_app(), name="mcp-sse")
    except Exception as exc:  # pragma: no cover
        print(f"[SearNXG] MCP SSE transport unavailable: {exc}")
    try:
        _mcp_http_app = _mcp_server.streamable_http_app(stateless_http=True)
        app.mount("/mcp-http", _mcp_http_app, name="mcp-http")
    except Exception as exc:  # pragma: no cover
        print(f"[SearNXG] MCP streamable HTTP transport unavailable: {exc}")
except Exception as exc:  # pragma: no cover - depends on optional package
    print(f"[SearNXG] MCP server unavailable: {exc}")


# ---------------------------------------------------------------------------
# Rate limiting for the browser UI endpoint
# ---------------------------------------------------------------------------
_rate_bucket: dict[str, list[float]] = {}


def _rate_limit(request: Request) -> None:
    settings = get_settings()
    if settings.rate_limit_per_minute <= 0:
        return
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    hits = [t for t in _rate_bucket.get(ip, []) if now - t < 60]
    if len(hits) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
    hits.append(now)
    _rate_bucket[ip] = hits


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _perform_search(req: SearchRequest, request: Request | None = None):
    settings = get_settings()
    if request is not None:
        require_api_key(request, settings)
    response = await execute_search(req, get_client(), settings)
    formatted = format_results(response, req.format)
    if req.format == "markdown":
        return PlainTextResponse(str(formatted), media_type="text/markdown")
    if req.format == "text":
        return PlainTextResponse(str(formatted))
    return JSONResponse(formatted)


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health():
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        uptime_seconds=int(time.time() - START_TIME),
        providers=settings.providers,
        mcp_enabled=_mcp_server is not None and settings.enable_mcp,
        cache_entries=len(_cache),
    )


@app.get("/api/config", tags=["System"])
async def config():
    return public_config()


@app.get("/api/setup", tags=["System"])
async def setup_status():
    """First-run state, written for humans rather than developers."""
    settings = get_settings()
    enabled = [
        name for name, on in settings.providers.items()
        if on and (name != "searxng" or settings.searxng_url.strip())
    ]
    first_run = is_first_run()
    checks = [
        {
            "id": "sources",
            "ok": len(enabled) >= 2,
            "title": "Search sources",
            "detail": (
                f"{len(enabled)} sources are ready to use."
                if len(enabled) >= 2
                else "Only one or no search sources are on. Turn on at least two."
            ),
        },
        {
            "id": "engine",
            "ok": True,
            "optional": True,
            "title": "Your own search engine",
            "detail": (
                "Connected to your SearXNG instance."
                if settings.searxng_url.strip()
                else "Not needed. Built-in sources already work. Add SearXNG any time."
            ),
        },
        {
            "id": "api",
            "ok": True,
            "title": "AI & app access",
            "detail": "The API and MCP tools are ready to use.",
        },
    ]
    return {
        "needs_setup": first_run or len(enabled) < 2,
        "first_run": first_run,
        "enabled_sources": enabled,
        "checks": checks,
    }


@app.post("/api/setup/quick", tags=["System"])
async def quick_setup():
    """Apply sensible defaults in one click, no technical choices required."""
    settings = get_settings()
    providers = dict(settings.providers)
    providers.update(
        {
            "bing": True,
            "duckduckgo": True,
            "wikipedia": True,
            "hackernews": True,
            "github": True,
            "searxng": bool(settings.searxng_url.strip()),
        }
    )
    updated = update_settings(
        {
            "providers": providers,
            "language": settings.language or "en",
            "default_limit": 10 if settings.default_limit < 5 else settings.default_limit,
            "require_api_key": False,
        }
    )
    return {"ok": True, "public": public_config(updated), "message": "Setup complete. You are ready to search."}


@app.post("/api/setup/searxng", tags=["System"])
async def setup_searxng(body: dict = Body(default_factory=dict)):
    """Validate and save a SearXNG URL from the beginner-friendly setup flow."""
    url = str(body.get("url") or "").strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Enter a full address starting with http:// or https://")
    base = get_settings()
    test_settings = base.model_copy(
        update={
            "searxng_url": url,
            "providers": {**base.providers, "searxng": True},
            "cache_ttl": 0,
        }
    )
    response = await execute_search(
        SearchRequest(query=f"SearNXG setup check {int(time.time())}", category="web", limit=3, providers=["searxng"]),
        get_client(),
        test_settings,
    )
    status = next((p for p in response.providers if p.provider == "searxng"), None)
    if not status or not status.ok:
        raise HTTPException(
            status_code=400,
            detail=(status.error if status else "Could not reach that address.") or "Could not reach that address.",
        )
    updated = update_settings(
        {"searxng_url": url, "providers": {**base.providers, "searxng": True}}
    )
    return {"ok": True, "public": public_config(updated), "message": "Your search engine is connected."}


@app.post("/api/search", tags=["Search"])
async def search_post(req: SearchRequest, request: Request):
    """Search the web. AI models can use this with an optional API key."""
    return await _perform_search(req, request)


@app.get("/api/search", tags=["Search"])
async def search_get(
    request: Request,
    q: str,
    category: str = "general",
    limit: int | None = None,
    page: int = 1,
    language: str | None = None,
    safesearch: bool | None = None,
    format: str = "json",
):
    """Same as POST /api/search, convenient for quick curl/agent calls."""
    req = SearchRequest(
        query=q,
        category=category,
        limit=limit,
        page=page,
        language=language,
        safesearch=safesearch,
        format=format,
    )
    return await _perform_search(req, request)


@app.post("/api/ui/search", tags=["Search"])
async def ui_search(req: SearchRequest, request: Request):
    """Browser UI endpoint — rate limited, never requires an API key."""
    _rate_limit(request)
    response = await execute_search(req, get_client(), get_settings())
    return response


@app.post("/api/extract", response_model=ExtractResponse, tags=["Search"])
async def extract(req: ExtractRequest, request: Request):
    """Fetch a URL and return readable Markdown content."""
    settings = get_settings()
    require_api_key(request, settings)
    if not settings.enable_extract:
        raise HTTPException(status_code=403, detail="Page extraction is disabled in settings.")
    try:
        data = await extract_url(req.url, get_client(), settings, req.max_chars)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch page: {exc}") from exc
    return ExtractResponse(**data)


# ---------------------------------------------------------------------------
# Settings & API keys
# ---------------------------------------------------------------------------
@app.get("/api/settings", tags=["Settings"])
async def get_all_settings(request: Request):
    require_admin(request, get_settings())
    return {
        "settings": get_settings().model_dump(),
        "provider_labels": PROVIDER_LABELS,
        "version": __version__,
        "settings_file": str(BASE_DIR / "data" / "settings.json"),
    }


@app.put("/api/settings", tags=["Settings"])
async def put_settings(patch: SettingsPatch, request: Request):
    require_admin(request, get_settings())
    updated = update_settings(patch.settings)
    return {"ok": True, "settings": updated.model_dump(), "public": public_config(updated)}


@app.post("/api/settings/test-searxng", response_model=TestConnectionResponse, tags=["Settings"])
async def test_searxng(
    request: Request,
    body: dict = Body(default_factory=dict),
):
    require_admin(request, get_settings())
    base = get_settings()
    url = str(body.get("url") or base.searxng_url).strip().rstrip("/")
    if not url:
        return TestConnectionResponse(ok=False, message="No SearXNG URL provided.")
    test_settings = base.model_copy(
        update={
            "searxng_url": url,
            "searxng_format": str(body.get("format") or base.searxng_format),
            "providers": {**base.providers, "searxng": True},
            "cache_ttl": 0,
        }
    )
    started = time.time()
    response = await execute_search(
        SearchRequest(
            query=f"SearNXG connection test {int(time.time())}",
            category="web",
            limit=3,
            providers=["searxng"],
        ),
        get_client(),
        test_settings,
    )
    status = next((p for p in response.providers if p.provider == "searxng"), None)
    ok = bool(status and status.ok)
    message = (
        f"Connected — {status.results} result(s) in {status.duration_ms} ms"
        if ok
        else f"Failed: {status.error if status else 'unknown error'}"
    )
    return TestConnectionResponse(
        ok=ok,
        message=message,
        result_count=status.results if status else 0,
        duration_ms=int((time.time() - started) * 1000),
    )


@app.get("/api/keys", tags=["Settings"])
async def list_keys(request: Request):
    require_admin(request, get_settings())
    keys = get_settings().api_keys
    return [
        {"key": key, "prefix": key[:8] + "…" if len(key) > 8 else key, "created_at": ""}
        for key in keys
    ]


@app.post("/api/keys", tags=["Settings"])
async def create_key(request: Request, body: CreateKeyRequest = CreateKeyRequest()):
    require_admin(request, get_settings())
    settings = get_settings()
    new_key = "sk-" + secrets.token_urlsafe(24)
    updated = update_settings({"api_keys": [*settings.api_keys, new_key]})
    return {"key": new_key, "prefix": new_key[:8] + "…", "total": len(updated.api_keys)}


@app.delete("/api/keys/{key:path}", tags=["Settings"])
async def delete_key(key: str, request: Request):
    require_admin(request, get_settings())
    settings = get_settings()
    remaining = [k for k in settings.api_keys if k != key]
    if len(remaining) == len(settings.api_keys):
        raise HTTPException(status_code=404, detail="Key not found.")
    update_settings({"api_keys": remaining})
    return {"ok": True, "total": len(remaining)}


# ---------------------------------------------------------------------------
# AI integration helpers
# ---------------------------------------------------------------------------
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the live web. Returns ranked results with title, URL, source "
                "and snippet. Use for any question requiring current or external information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."},
                    "limit": {"type": "integer", "description": "Number of results (1-20).", "default": 5},
                    "category": {
                        "type": "string",
                        "enum": ["general", "web", "news", "wiki", "code", "discussions"],
                        "default": "general",
                    },
                    "language": {"type": "string", "description": "Language code, e.g. 'en'.", "default": "en"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Fetch a URL and return the page's main readable content as Markdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full http(s) URL to read."},
                    "max_chars": {"type": "integer", "description": "Max characters to return.", "default": 8000},
                },
                "required": ["url"],
            },
        },
    },
]


@app.get("/api/tools/openai", tags=["AI Integration"])
async def openai_tools():
    return OPENAI_TOOLS


@app.get("/api/tools/mcp", tags=["AI Integration"])
async def mcp_config(request: Request):
    base = str(request.base_url).rstrip("/")
    sse_url = f"{base}/mcp/sse"
    stream_url = f"{base}/mcp-http/mcp"
    return {
        "enabled": _mcp_server is not None and get_settings().enable_mcp,
        "servers": {
            "searnxg-sse": {
                "command": "npx",
                "args": ["-y", "mcp-remote", sse_url],
            },
            "searnxg-http": {"url": stream_url, "transport": "streamable-http"},
        },
        "tools": ["web_search", "fetch_url", "list_sources"],
    }


# ---------------------------------------------------------------------------
# Frontend (served when frontend/dist has been built)
# ---------------------------------------------------------------------------
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str):
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return HTMLResponse(
        """
        <!doctype html><html><head><title>SearNXG</title>
        <style>body{font-family:system-ui;background:#0b0d12;color:#e8ecf4;display:grid;
        place-items:center;min-height:100vh;margin:0}code{color:#7dd3fc}</style></head>
        <body><div><h1>SearNXG backend is running</h1>
        <p>Build the UI with <code>cd frontend && npm install && npm run build</code>,
        or run <code>npm run dev</code> for hot reload.</p>
        <p><a href="/api/docs" style="color:#7dd3fc">API docs</a> ·
        <a href="/api/health" style="color:#7dd3fc">Health</a></p></div></body></html>
        """
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
