"""Shared helpers for search providers."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx

from ..models import SearchResult

if TYPE_CHECKING:
    from ..config import AppSettings

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "gbraid", "wbraid", "msclkid", "ref", "ref_src",
}

# Which providers serve which categories.
CATEGORY_PROVIDERS: dict[str, list[str]] = {
    "general": ["searxng", "bing", "duckduckgo", "wikipedia", "hackernews"],
    "web": ["searxng", "bing", "duckduckgo"],
    "news": ["hackernews", "bing", "searxng"],
    "wiki": ["wikipedia"],
    "code": ["github", "searxng"],
    "discussions": ["hackernews", "searxng"],
}


@dataclass
class SearchContext:
    query: str
    limit: int
    page: int
    language: str
    safesearch: bool
    time_range: str
    category: str
    client: httpx.AsyncClient
    settings: "AppSettings"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.settings.user_agent,
            "Accept-Language": f"{self.language},en;q=0.8" if self.language else "en-US,en;q=0.9",
        }

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def clean_text(value: str | None, max_len: int = 600) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
    return value[:max_len]


def normalize_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        query = [
            (k, v) for k, v in (
                part.split("=", 1) if "=" in part else (part, "")
                for part in parsed.query.split("&") if part
            )
            if k.lower() not in TRACKING_PARAMS
        ]
        path = parsed.path.rstrip("/") or "/"
        return urlunparse(("", host, path, "", urlencode(query), ""))
    except Exception:
        return url.strip().lower()


def domain_of(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def favicon_for(url: str) -> str | None:
    domain = domain_of(url)
    return f"https://icons.duckduckgo.com/ip3/{domain}.ico" if domain else None


def make_result(
    title: str,
    url: str,
    content: str,
    engine: str,
    category: str = "general",
    published_date: str | None = None,
    score: float = 0.0,
) -> SearchResult:
    return SearchResult(
        title=clean_text(title, 300) or url,
        url=url,
        content=clean_text(content),
        engine=engine,
        category=category,
        published_date=published_date,
        favicon=favicon_for(url),
        score=score,
    )


def decode_bing_url(href: str) -> str:
    """Bing wraps result URLs in /ck/a?...&u=a1<base64url>."""
    try:
        parsed = urlparse(href)
        if "bing.com" not in parsed.netloc:
            return href
        values = parse_qs(parsed.query)
        raw = values.get("u", [""])[0]
        if raw.startswith("a1"):
            encoded = raw[2:]
            encoded += "=" * (-len(encoded) % 4)
            decoded = base64.urlsafe_b64decode(encoded).decode("utf-8", errors="ignore")
            if decoded.startswith(("http://", "https://")):
                return decoded
    except Exception:
        pass
    return href


def time_range_query(value: str, field: str = "time") -> str:
    """Translate a time range into engine-specific query syntax where useful."""
    mapping = {"day": "1d", "week": "1w", "month": "1m", "year": "1y"}
    if not value or value not in mapping:
        return ""
    if field == "duckduckgo":
        return f"df:{mapping[value]}"
    return ""
