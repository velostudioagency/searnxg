"""Hacker News (Algolia) provider — great for tech news and discussions."""

from __future__ import annotations

import time

from .base import SearchContext, clean_text, make_result

DAY = 86400
RANGE_DAYS = {"day": 1, "week": 7, "month": 30, "year": 365}


async def search(ctx: SearchContext) -> list:
    endpoint = (
        "https://hn.algolia.com/api/v1/search_by_date"
        if ctx.category == "news"
        else "https://hn.algolia.com/api/v1/search"
    )
    params: dict[str, str | int] = {
        "query": ctx.query,
        "tags": "story",
        "hitsPerPage": min(ctx.limit, 50),
        "page": max(0, ctx.page - 1),
    }
    if ctx.time_range in RANGE_DAYS:
        params["numericFilters"] = f"created_at_i>{int(time.time()) - RANGE_DAYS[ctx.time_range] * DAY}"

    response = await ctx.client.get(endpoint, params=params, headers=ctx.headers)
    response.raise_for_status()
    payload = response.json()

    results = []
    for hit in payload.get("hits", []):
        object_id = hit.get("objectID") or ""
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
        if not url.startswith(("http://", "https://")):
            url = f"https://news.ycombinator.com/item?id={object_id}"
        raw_snippet = hit.get("story_text") or hit.get("comment_text") or ""
        meta = []
        if hit.get("points"):
            meta.append(f"{hit['points']} points")
        if hit.get("num_comments") is not None:
            meta.append(f"{hit['num_comments']} comments")
        snippet = clean_text(raw_snippet, 400)
        if meta:
            snippet = f"[{' · '.join(meta)}] {snippet}".strip()
        results.append(
            make_result(
                hit.get("title") or "",
                url,
                snippet,
                "Hacker News",
                ctx.category,
                (hit.get("created_at") or "")[:10] or None,
            )
        )
    return results[: ctx.limit]
