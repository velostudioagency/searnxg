"""Search provider modules and their shared context."""

from . import bing, duckduckgo, github, hackernews, searxng, wikipedia
from .base import CATEGORY_PROVIDERS, SearchContext, clean_text, favicon_for, make_result, normalize_url

# Aliases so callers can write providers.BingProvider.search(...) etc.
BingProvider = bing
DuckDuckGoProvider = duckduckgo
GithubProvider = github
HackerNewsProvider = hackernews
SearXNGProvider = searxng
WikipediaProvider = wikipedia

__all__ = [
    "SearchContext",
    "clean_text",
    "favicon_for",
    "make_result",
    "normalize_url",
    "CATEGORY_PROVIDERS",
    "BingProvider",
    "DuckDuckGoProvider",
    "GithubProvider",
    "HackerNewsProvider",
    "SearXNGProvider",
    "WikipediaProvider",
]
