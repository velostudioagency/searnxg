"""Pydantic schemas shared by the REST API, MCP tools and the web UI."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

CATEGORIES = ("general", "web", "news", "wiki", "code", "discussions")


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    category: str = "general"
    limit: int | None = Field(default=None, ge=1, le=200)
    page: int = Field(default=1, ge=1, le=20)
    language: str | None = None
    safesearch: bool | None = None
    time_range: str | None = None
    providers: list[str] | None = None
    engines: list[str] | None = None  # alias used by some SearXNG clients
    format: str = "json"  # json | markdown | text

    @field_validator("query")
    @classmethod
    def _clean_query(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("query must not be empty")
        return value

    @field_validator("category")
    @classmethod
    def _clean_category(cls, value: str) -> str:
        value = (value or "general").lower()
        return value if value in CATEGORIES else "general"

    @field_validator("format")
    @classmethod
    def _clean_format(cls, value: str) -> str:
        value = (value or "json").lower()
        return value if value in {"json", "markdown", "text"} else "json"


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    engine: str
    category: str = "general"
    published_date: str | None = None
    favicon: str | None = None
    score: float = 0.0


class ProviderStatus(BaseModel):
    provider: str
    ok: bool
    results: int = 0
    duration_ms: int = 0
    error: str | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    number_of_results: int
    took_ms: int
    providers: list[ProviderStatus]
    page: int = 1
    language: str
    safesearch: bool
    category: str
    cached: bool = False


class ExtractRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2000)
    max_chars: int | None = Field(default=None, ge=500, le=100000)
    format: str = "markdown"

    @field_validator("url")
    @classmethod
    def _check_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return value


class ExtractResponse(BaseModel):
    url: str
    final_url: str
    title: str
    site_name: str
    author: str | None = None
    published_date: str | None = None
    text: str
    word_count: int
    fetched_at: str
    duration_ms: int


class ApiKeyInfo(BaseModel):
    key: str
    prefix: str
    created_at: str


class CreateKeyRequest(BaseModel):
    label: str = "key"


class SettingsPatch(BaseModel):
    settings: dict[str, Any]


class TestConnectionResponse(BaseModel):
    ok: bool
    message: str
    result_count: int = 0
    duration_ms: int = 0


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: int
    providers: dict[str, bool]
    mcp_enabled: bool
    cache_entries: int
