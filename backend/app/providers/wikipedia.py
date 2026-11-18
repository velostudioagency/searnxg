"""Wikipedia search provider (REST search API with MediaWiki API fallback)."""

from __future__ import annotations

from urllib.parse import quote

from bs4 import BeautifulSoup

from .base import SearchContext, make_result

REST_API = "https://en.wikipedia.org/w/rest.php/v1/search/page"
MW_API = "https://en.wikipedia.org/w/api.php"
WIKI_UA = "SearNXG/1.0 (web search application; contact: admin@localhost)"


def _headers(ctx: SearchContext) -> dict[str, str]:
    return {**ctx.headers, "User-Agent": WIKI_UA, "Accept": "application/json"}


def _clean_excerpt(value: str) -> str:
    return BeautifulSoup(value or "", "lxml").get_text(" ", strip=True)


async def search(ctx: SearchContext) -> list:
    response = await ctx.client.get(
        REST_API,
        params={"q": ctx.query, "limit": min(ctx.limit, 20)},
        headers=_headers(ctx),
    )
    if response.status_code == 200:
        results = []
        payload = response.json()
        for page in payload.get("pages", []):
            key = page.get("key") or ""
            title = page.get("title") or ""
            if not key or not title:
                continue
            snippet = _clean_excerpt(page.get("excerpt") or "")
            description = page.get("description") or ""
            if description:
                snippet = f"{description} — {snippet}".strip(" —")
            results.append(
                make_result(title, f"https://en.wikipedia.org/wiki/{key}", snippet, "Wikipedia", ctx.category)
            )
        if results:
            return results[: ctx.limit]

    # Fallback for instances where the REST endpoint is unavailable.
    response = await ctx.client.get(
        MW_API,
        params={
            "action": "query",
            "list": "search",
            "srsearch": ctx.query,
            "srlimit": min(ctx.limit, 20),
            "srnamespace": 0,
            "format": "json",
            "formatversion": 2,
        },
        headers=_headers(ctx),
    )
    response.raise_for_status()

    results = []
    for hit in response.json().get("query", {}).get("search", []):
        title = hit.get("title") or ""
        if not title:
            continue
        url = "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_"), safe="()_/")
        results.append(
            make_result(
                title, url, _clean_excerpt(hit.get("snippet") or ""), "Wikipedia", ctx.category,
                (hit.get("timestamp") or "")[:10] or None,
            )
        )
    return results[: ctx.limit]
