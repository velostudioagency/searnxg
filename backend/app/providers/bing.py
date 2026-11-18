"""Bing provider — uses the clean RSS feed with an HTML-scraping fallback."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from .base import SearchContext, clean_text, decode_bing_url, make_result

FRESHNESS = {
    "day": 'ex1:"ez1"',
    "week": 'ex1:"ez2"',
    "month": 'ex1:"ez3"',
    "year": 'ex1:"ez4"',
}


def _base_params(ctx: SearchContext) -> dict:
    params: dict[str, str | int] = {
        "q": ctx.query,
        "setlang": ctx.language or "en",
        "count": min(ctx.limit * 2, 50),
        "first": ctx.offset + 1,
    }
    if ctx.safesearch:
        params["safeSearch"] = "Strict"
    if ctx.time_range in FRESHNESS:
        params["filters"] = FRESHNESS[ctx.time_range]
    return params


def _parse_rss(body: str, ctx: SearchContext) -> list:
    results = []
    root = ET.fromstring(body)
    for item in root.findall(".//item"):
        url = clean_text(item.findtext("link") or "")
        if not url.startswith(("http://", "https://")):
            continue
        results.append(
            make_result(
                item.findtext("title") or "",
                url,
                item.findtext("description") or "",
                "Bing",
                ctx.category,
                (item.findtext("pubDate") or "")[:40] or None,
            )
        )
    return results


def _parse_html(body: str, ctx: SearchContext) -> list:
    soup = BeautifulSoup(body, "lxml")
    results = []
    for item in soup.select("li.b_algo"):
        anchor = item.select_one("h2 a")
        if not anchor:
            continue
        url = decode_bing_url(anchor.get("href", ""))
        if not url.startswith(("http://", "https://")):
            continue
        snippet_el = item.select_one(".b_caption p") or item.select_one("p.b_lineclamp2")
        snippet = clean_text(snippet_el.get_text(" ", strip=True)) if snippet_el else ""
        cite = item.select_one("cite")
        if cite and snippet:
            snippet = f"{clean_text(cite.get_text(' ', strip=True))} — {snippet}"
        date_el = item.select_one(".b_factrow")
        published = clean_text(date_el.get_text(" ", strip=True))[:60] if date_el else None
        results.append(
            make_result(anchor.get_text(" ", strip=True), url, snippet, "Bing", ctx.category, published)
        )
    return results


async def search(ctx: SearchContext) -> list:
    response = await ctx.client.get(
        "https://www.bing.com/search",
        params={**_base_params(ctx), "format": "rss"},
        headers=ctx.headers,
    )
    response.raise_for_status()

    results: list = []
    if "<rss" in response.text[:2000]:
        try:
            results = _parse_rss(response.text, ctx)
        except ET.ParseError:
            results = []
    if not results:
        # The RSS feed is occasionally rate limited — fall back to HTML.
        html = await ctx.client.get(
            "https://www.bing.com/search", params=_base_params(ctx), headers=ctx.headers
        )
        html.raise_for_status()
        results = _parse_html(html.text, ctx)

    return results[: ctx.limit]
