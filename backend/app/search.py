"""Search orchestration: run providers in parallel, merge, rank, cache."""

from __future__ import annotations

import asyncio
import json
import math
import time
from typing import Any

import httpx

from . import providers
from .config import AppSettings
from .offline import offline_results
from .models import (
    ProviderStatus,
    SearchRequest,
    SearchResponse,
    SearchResult,
)

PROVIDER_FUNCS = {
    "searxng": providers.SearXNGProvider.search,
    "bing": providers.BingProvider.search,
    "duckduckgo": providers.DuckDuckGoProvider.search,
    "wikipedia": providers.WikipediaProvider.search,
    "hackernews": providers.HackerNewsProvider.search,
    "github": providers.GithubProvider.search,
}

SOURCE_WEIGHT = {
    "Bing": 4.0,
    "DuckDuckGo": 4.0,
    "Wikipedia": 3.0,
    "GitHub": 2.0,
    "Hacker News": 2.0,
}

_cache: dict[str, tuple[float, SearchResponse]] = {}


def _cache_key(req: SearchRequest, settings: AppSettings) -> str:
    return json.dumps(
        {
            "q": req.query,
            "c": req.category,
            "l": req.limit,
            "p": req.page,
            "lang": req.language or settings.language,
            "safe": req.safesearch if req.safesearch is not None else settings.safesearch,
            "t": req.time_range or settings.time_range,
            "providers": sorted(req.providers or req.engines or []),
        },
        sort_keys=True,
    )


async def _run_provider(name: str, ctx: providers.SearchContext) -> tuple[str, list, str | None, int]:
    started = time.perf_counter()
    try:
        results = await asyncio.wait_for(
            PROVIDER_FUNCS[name](ctx), timeout=ctx.settings.timeout
        )
        return name, list(results), None, int((time.perf_counter() - started) * 1000)
    except asyncio.TimeoutError:
        return name, [], "This source was too slow to answer.", int((time.perf_counter() - started) * 1000)
    except Exception as exc:  # noqa: BLE001 - providers must never break the whole search
        message = str(exc).strip() or exc.__class__.__name__
        lower = message.lower()
        if "challenge" in lower or "403" in lower or "429" in lower or "robot policy" in lower:
            message = "This source is blocking automated requests right now."
        elif "timed out" in lower or "timeout" in lower:
            message = "This source was too slow to answer."
        elif "404" in lower:
            message = "This source could not be reached. Check its URL in Settings."
        return name, [], message[:200], int((time.perf_counter() - started) * 1000)


def _rank(results: list[SearchResult], query: str) -> list[SearchResult]:
    terms = [t.lower() for t in query.split() if len(t) > 1]
    scored: list[SearchResult] = []
    for result in results:
        title = result.title.lower()
        content = result.content.lower()
        base = math.log10(max(result.score, 1)) if result.engine == "GitHub" else min(result.score, 100) / 50
        points = SOURCE_WEIGHT.get(result.engine, 1.0) + base
        if terms:
            if all(t in title for t in terms):
                points += 8
            elif any(t in title for t in terms):
                points += 3
            if any(t in content for t in terms):
                points += 1.5
        if len(result.content) > 80:
            points += 1
        result.score = round(points, 2)
        scored.append(result)
    return sorted(scored, key=lambda r: r.score, reverse=True)


def _dedupe(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    unique: list[SearchResult] = []
    for result in results:
        key = providers.normalize_url(result.url)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(result)
    return unique


async def execute_search(
    req: SearchRequest, client: httpx.AsyncClient, settings: AppSettings
) -> SearchResponse:
    started = time.perf_counter()
    limit = min(req.limit or settings.default_limit, settings.max_limit)
    language = req.language or settings.language
    safesearch = req.safesearch if req.safesearch is not None else settings.safesearch
    time_range = req.time_range if req.time_range is not None else settings.time_range

    cache_key = _cache_key(req, settings)
    if settings.cache_ttl > 0:
        cached = _cache.get(cache_key)
        if cached and time.time() - cached[0] < settings.cache_ttl:
            response = cached[1].model_copy(update={"cached": True})
            return response

    selected = req.providers or req.engines or providers.CATEGORY_PROVIDERS.get(
        req.category, providers.CATEGORY_PROVIDERS["general"]
    )
    selected = [name for name in dict.fromkeys(selected) if name in PROVIDER_FUNCS]

    ctx = providers.SearchContext(
        query=req.query,
        limit=limit,
        page=req.page,
        language=language,
        safesearch=safesearch,
        time_range=time_range,
        category=req.category,
        client=client,
        settings=settings,
    )

    tasks: dict[str, asyncio.Task] = {}
    statuses: list[ProviderStatus] = []
    for name in selected:
        if not settings.providers.get(name, False):
            statuses.append(ProviderStatus(provider=name, ok=False, error="disabled in settings"))
            continue
        if name == "searxng" and not settings.searxng_url.strip():
            statuses.append(ProviderStatus(provider=name, ok=False, error="no instance URL configured"))
            continue
        tasks[name] = asyncio.create_task(_run_provider(name, ctx))

    if tasks:
        completed = await asyncio.gather(*tasks.values())
        for name, (_, found, error, duration) in zip(tasks.keys(), completed):
            statuses.append(
                ProviderStatus(
                    provider=name,
                    ok=error is None,
                    results=len(found),
                    duration_ms=duration,
                    error=error,
                )
            )
        collected = [result for _, found, _, _ in completed for result in found]
    else:
        collected = []

    # Last line of defence: never leave the user with an empty screen because
    # every external source happens to be blocked or offline.
    if not collected:
        fallback = offline_results(req.query, limit)
        if fallback:
            collected = fallback
            statuses.append(
                ProviderStatus(
                    provider="offline",
                    ok=True,
                    results=len(fallback),
                    duration_ms=0,
                    error="Built-in library. Live sources were unavailable.",
                )
            )

    ranked = _rank(_dedupe(collected), req.query)[:limit]
    response = SearchResponse(
        query=req.query,
        results=ranked,
        number_of_results=len(ranked),
        took_ms=int((time.perf_counter() - started) * 1000),
        providers=statuses,
        page=req.page,
        language=language,
        safesearch=safesearch,
        category=req.category,
        cached=False,
    )

    if settings.cache_ttl > 0:
        # Prune stale entries while we are here.
        now = time.time()
        if len(_cache) > 500:
            for key in list(_cache):
                if now - _cache[key][0] > settings.cache_ttl:
                    _cache.pop(key, None)
        _cache[cache_key] = (now, response)
    return response


def format_results(response: SearchResponse, fmt: str = "json") -> Any:
    if fmt == "json":
        return response.model_dump()
    lines: list[str] = []
    if fmt == "markdown":
        lines.append(f"## Search results for: {response.query}\n")
        for idx, r in enumerate(response.results, 1):
            lines.append(f"{idx}. **[{r.title}]({r.url})**")
            lines.append(f"   - Source: {r.engine}")
            if r.published_date:
                lines.append(f"   - Published: {r.published_date}")
            lines.append(f"   - {r.content}\n")
        return "\n".join(lines)
    for idx, r in enumerate(response.results, 1):
        lines.append(f"{idx}. {r.title}\n   {r.url}\n   [{r.engine}] {r.content}\n")
    return "\n".join(lines)
