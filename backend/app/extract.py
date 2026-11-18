"""Fetch a URL and extract clean, readable content (great for RAG / agents)."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup

from .config import AppSettings


async def extract_url(
    url: str, client: httpx.AsyncClient, settings: AppSettings, max_chars: int | None = None
) -> dict:
    started = time.perf_counter()
    limit = min(max_chars or settings.max_extract_chars, 100000)
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    response = await client.get(url, headers=headers, follow_redirects=True)
    response.raise_for_status()
    html = response.text

    text = ""
    meta = None
    try:
        text = (
            trafilatura.extract(
                html,
                url=url,
                output_format="markdown",
                include_comments=False,
                include_tables=True,
                favor_recall=True,
            )
            or ""
        )
        meta = trafilatura.extract_metadata(html, default_url=url)
    except Exception:
        text = ""

    if not text.strip():
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        body = soup.get_text("\n", strip=True)
        text = f"# {title}\n\n{body}" if title else body

    title = getattr(meta, "title", None) or ""
    if not title:
        soup = BeautifulSoup(html, "lxml")
        title = soup.title.get_text(" ", strip=True) if soup.title else urlparse(url).netloc

    text = text.strip()[:limit]
    return {
        "url": url,
        "final_url": str(response.url),
        "title": title[:300],
        "site_name": (getattr(meta, "sitename", None) or urlparse(str(response.url)).netloc)[:120],
        "author": (getattr(meta, "author", None) or None),
        "published_date": (getattr(meta, "date", None) or None),
        "text": text,
        "word_count": len(text.split()),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": int((time.perf_counter() - started) * 1000),
    }
