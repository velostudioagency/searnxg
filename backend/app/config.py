"""Persistent, runtime-updatable application settings."""

from __future__ import annotations

import json
import os
import secrets
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

# Captured before anything is saved on startup. Once settings are written,
# this flips to False for the lifetime of the process.
FIRST_RUN = not SETTINGS_FILE.exists()

VERSION = "1.0.0"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_PROVIDERS: dict[str, bool] = {
    "bing": True,
    "duckduckgo": True,
    "wikipedia": True,
    "hackernews": True,
    "github": True,
    "searxng": False,
}

PROVIDER_LABELS: dict[str, str] = {
    "bing": "Bing",
    "duckduckgo": "DuckDuckGo",
    "wikipedia": "Wikipedia",
    "hackernews": "Hacker News",
    "github": "GitHub",
    "searxng": "SearXNG",
}


class AppSettings(BaseModel):
    """All settings exposed in the Settings panel of the UI."""

    # Search engine
    searxng_url: str = ""
    searxng_api_key: str = ""
    searxng_format: str = "auto"  # auto | json | html
    providers: dict[str, bool] = Field(default_factory=lambda: dict(DEFAULT_PROVIDERS))
    default_limit: int = 10
    max_limit: int = 50
    timeout: float = 12.0
    language: str = "en"
    safesearch: bool = False
    time_range: str = ""  # "", day, week, month, year
    cache_ttl: int = 300

    # API & security
    api_keys: list[str] = Field(
        default_factory=lambda: ["dev-" + secrets.token_urlsafe(14)]
    )
    require_api_key: bool = False
    admin_key: str = ""
    enable_extract: bool = True
    max_extract_chars: int = 12000

    # MCP
    enable_mcp: bool = True

    # App
    theme: str = "dark"
    user_agent: str = DEFAULT_USER_AGENT
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    rate_limit_per_minute: int = 60
    version: str = VERSION

    @field_validator("providers")
    @classmethod
    def _merge_providers(cls, value: dict[str, bool]) -> dict[str, bool]:
        merged = dict(DEFAULT_PROVIDERS)
        merged.update(value or {})
        return {k: bool(v) for k, v in merged.items() if k in DEFAULT_PROVIDERS}

    @field_validator("default_limit")
    @classmethod
    def _limit(cls, value: int) -> int:
        return max(1, min(100, int(value)))

    @field_validator("max_limit")
    @classmethod
    def _max_limit(cls, value: int) -> int:
        return max(1, min(200, int(value)))

    @field_validator("timeout")
    @classmethod
    def _timeout(cls, value: float) -> float:
        return max(1.0, min(60.0, float(value)))

    @field_validator("cache_ttl")
    @classmethod
    def _cache(cls, value: int) -> int:
        return max(0, min(86400, int(value)))


def _apply_env(settings: AppSettings) -> AppSettings:
    """Environment variables override saved file values when present."""
    data = settings.model_dump()

    if os.getenv("SEARXNG_URL"):
        data["searxng_url"] = os.environ["SEARXNG_URL"].rstrip("/")
        data["providers"] = {**data["providers"], "searxng": True}
    if os.getenv("SEARXNG_API_KEY"):
        data["searxng_api_key"] = os.environ["SEARXNG_API_KEY"]
    if os.getenv("API_KEYS"):
        data["api_keys"] = [k.strip() for k in os.environ["API_KEYS"].split(",") if k.strip()]
    if os.getenv("ADMIN_KEY"):
        data["admin_key"] = os.environ["ADMIN_KEY"]
    if os.getenv("REQUIRE_API_KEY"):
        data["require_api_key"] = os.environ["REQUIRE_API_KEY"].lower() in {"1", "true", "yes"}
    if os.getenv("DEFAULT_LIMIT"):
        data["default_limit"] = int(os.environ["DEFAULT_LIMIT"])
    if os.getenv("TIMEOUT"):
        data["timeout"] = float(os.environ["TIMEOUT"])

    return AppSettings(**data)


def load_settings() -> AppSettings:
    data: dict[str, Any] = {}
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
    return _apply_env(AppSettings(**data))


def save_settings(settings: AppSettings) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(settings.model_dump(), indent=2, ensure_ascii=False)
    # Atomic write so a crash never leaves a half-written settings file.
    fd, tmp_name = tempfile.mkstemp(dir=SETTINGS_FILE.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_name, SETTINGS_FILE)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


# Module-level live settings, refreshed by main.py on startup and by the API.
_current: AppSettings | None = None


def get_settings() -> AppSettings:
    global _current
    if _current is None:
        _current = load_settings()
    return _current


def set_settings(settings: AppSettings, mark_configured: bool = False) -> AppSettings:
    global _current, FIRST_RUN
    _current = settings
    save_settings(settings)
    if mark_configured:
        FIRST_RUN = False
    return _current


def is_first_run() -> bool:
    return FIRST_RUN


def update_settings(patch: dict[str, Any]) -> AppSettings:
    current = get_settings().model_dump()
    for key, value in patch.items():
        if key in current:
            current[key] = value
    return set_settings(AppSettings(**current), mark_configured=True)


def public_config(settings: AppSettings | None = None) -> dict[str, Any]:
    """Settings that are safe to expose to the browser / unauthenticated callers."""
    s = settings or get_settings()
    return {
        "version": s.version,
        "providers": s.providers,
        "provider_labels": PROVIDER_LABELS,
        "default_limit": s.default_limit,
        "max_limit": s.max_limit,
        "language": s.language,
        "safesearch": s.safesearch,
        "time_range": s.time_range,
        "require_api_key": s.require_api_key,
        "auth_required": s.require_api_key and bool(s.api_keys),
        "mcp_enabled": s.enable_mcp,
        "extract_enabled": s.enable_extract,
        "theme": s.theme,
        "searxng_configured": bool(s.searxng_url.strip()),
        "rate_limit_per_minute": s.rate_limit_per_minute,
    }
