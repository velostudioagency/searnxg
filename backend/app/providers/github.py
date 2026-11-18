"""GitHub repository search provider — used for the 'code' category."""

from __future__ import annotations

from .base import SearchContext, clean_text, make_result

API = "https://api.github.com/search/repositories"


async def search(ctx: SearchContext) -> list:
    headers = {
        **ctx.headers,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    response = await ctx.client.get(
        API,
        params={
            "q": ctx.query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(ctx.limit, 50),
            "page": ctx.page,
        },
        headers=headers,
    )
    response.raise_for_status()
    payload = response.json()

    results = []
    for repo in payload.get("items", []):
        description = clean_text(repo.get("description") or "", 500)
        stars = repo.get("stargazers_count") or 0
        language = repo.get("language") or ""
        meta = [f"★ {stars:,}"] if stars else []
        if language:
            meta.append(language)
        if meta:
            description = f"[{' · '.join(meta)}] {description}".strip()
        results.append(
            make_result(
                repo.get("full_name") or "",
                repo.get("html_url") or "",
                description,
                "GitHub",
                ctx.category,
                (repo.get("updated_at") or "")[:10] or None,
                score=float(stars),
            )
        )
    return results[: ctx.limit]
