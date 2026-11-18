"""SearXNG provider — uses the user's own instance when configured."""

from __future__ import annotations

from bs4 import BeautifulSoup

from .base import SearchContext, clean_text, make_result

SAFESEARCH_NUM = {"off": 0, "moderate": 1, "strict": 2}


def _params(ctx: SearchContext, fmt: str) -> dict:
    params: dict = {
        "q": ctx.query,
        "format": fmt,
        "language": ctx.language or "all",
        "safesearch": 1 if ctx.safesearch else 0,
        "pageno": ctx.page,
        "categories": "general" if ctx.category in {"general", "web"} else ctx.category,
    }
    if ctx.time_range:
        params["time_range"] = ctx.time_range
    return params


def _headers(ctx: SearchContext) -> dict[str, str]:
    headers = dict(ctx.headers)
    if ctx.settings.searxng_api_key:
        headers["X-API-Key"] = ctx.settings.searxng_api_key
        headers["Authorization"] = f"Bearer {ctx.settings.searxng_api_key}"
    return headers


async def _search_json(ctx: SearchContext) -> list:
    response = await ctx.client.get(
        f"{ctx.settings.searxng_url.rstrip('/')}/search",
        params=_params(ctx, "json"),
        headers=_headers(ctx),
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "json" not in content_type and not response.text.lstrip().startswith("{"):
        raise RuntimeError("SearXNG JSON format is disabled on this instance")
    payload = response.json()
    results = []
    for hit in payload.get("results", []):
        url = hit.get("url") or ""
        if not url.startswith(("http://", "https://")):
            continue
        results.append(
            make_result(
                hit.get("title") or "",
                url,
                hit.get("content") or "",
                hit.get("engine") or "SearXNG",
                ctx.category,
                hit.get("publishedDate"),
                score=float(hit.get("score") or 0),
            )
        )
    return results[: ctx.limit]


async def _search_html(ctx: SearchContext) -> list:
    response = await ctx.client.get(
        f"{ctx.settings.searxng_url.rstrip('/')}/search",
        params=_params(ctx, "html"),
        headers=_headers(ctx),
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    results = []
    for article in soup.select("article.result, div.result"):
        anchor = article.select_one("h3 a") or article.select_one("a.url_header")
        if not anchor:
            continue
        url = clean_text(anchor.get("href", ""))
        if not url.startswith(("http://", "https://")):
            continue
        content_el = article.select_one(".content") or article.select_one("p.content")
        engine_el = article.select_one(".engine") or article.select_one("span.engine")
        url_el = article.select_one(".url_wrapper") or article.select_one("span.url")
        content = clean_text(content_el.get_text(" ", strip=True)) if content_el else ""
        if url_el and content:
            content = f"{clean_text(url_el.get_text(' ', strip=True))} — {content}"
        engine = clean_text(engine_el.get_text(" ", strip=True)) if engine_el else "SearXNG"
        results.append(make_result(anchor.get_text(" ", strip=True), url, content, engine, ctx.category))
    return results[: ctx.limit]


async def search(ctx: SearchContext) -> list:
    if not ctx.settings.searxng_url.strip():
        raise RuntimeError("SearXNG URL is not configured")
    mode = (ctx.settings.searxng_format or "auto").lower()
    if mode == "json":
        return await _search_json(ctx)
    if mode == "html":
        return await _search_html(ctx)
    try:
        return await _search_json(ctx)
    except Exception:
        return await _search_html(ctx)
