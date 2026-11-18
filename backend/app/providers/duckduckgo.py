"""DuckDuckGo HTML / Lite provider (no API key required)."""

from __future__ import annotations

from bs4 import BeautifulSoup

from .base import SearchContext, clean_text, make_result, time_range_query


async def search(ctx: SearchContext) -> list:
    query = ctx.query
    suffix = time_range_query(ctx.time_range, "duckduckgo")
    if suffix:
        query = f"{query} {suffix}"

    headers = {**ctx.headers, "Accept": "text/html,application/xhtml+xml"}
    response = await ctx.client.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query, "kl": "us-en" if ctx.language == "en" else ctx.language},
        headers=headers,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    if "anomaly-modal" in response.text or "challenge-form" in response.text:
        raise RuntimeError("DuckDuckGo bot challenge")

    results = []
    for item in soup.select("div.result, div.web-result"):
        anchor = item.select_one("a.result__a")
        if not anchor:
            continue
        url = clean_text(anchor.get("href", ""))
        if not url.startswith(("http://", "https://")):
            continue
        snippet_el = item.select_one("a.result__snippet") or item.select_one(".result__snippet")
        snippet = clean_text(snippet_el.get_text(" ", strip=True)) if snippet_el else ""
        results.append(
            make_result(clean_text(anchor.get_text(" ", strip=True)), url, snippet, "DuckDuckGo", ctx.category)
        )

    if results:
        return results[: ctx.limit]

    # Lite markup as a second chance.
    lite = await ctx.client.get(
        "https://lite.duckduckgo.com/lite/", params={"q": query}, headers=headers
    )
    lite.raise_for_status()
    if "anomaly-modal" in lite.text or "challenge-form" in lite.text:
        raise RuntimeError("DuckDuckGo bot challenge")
    lite_soup = BeautifulSoup(lite.text, "lxml")
    for anchor in lite_soup.select("a.result-link"):
        url = clean_text(anchor.get("href", ""))
        if not url.startswith(("http://", "https://")):
            continue
        row = anchor.find_parent("tr")
        snippet = ""
        if row:
            snip = row.find_next_sibling("tr")
            if snip:
                td = snip.select_one("td.result-snippet")
                snippet = clean_text(td.get_text(" ", strip=True)) if td else ""
        results.append(
            make_result(clean_text(anchor.get_text(" ", strip=True)), url, snippet, "DuckDuckGo", ctx.category)
        )

    return results[: ctx.limit]
