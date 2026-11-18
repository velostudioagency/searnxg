"""Model Context Protocol server exposing web search + page reading as tools."""

from __future__ import annotations

import json
from typing import Any, Callable

try:  # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # MCP SDK 1.x
    from mcp.server.fastmcp import FastMCP

from .extract import extract_url
from .models import SearchRequest
from .search import execute_search, format_results


def create_mcp_server(
    get_client: Callable,
    get_settings: Callable,
) -> Any:
    """Build an MCP server instance bound to the running app's client/settings."""

    mcp = FastMCP(
        "SearNXG",
        instructions=(
            "Web search and page-reading tools powered by SearNXG. "
            "Use web_search to find current information on the internet and "
            "fetch_url to read the full contents of a result."
        ),
    )

    @mcp.tool()
    async def web_search(
        query: str,
        limit: int = 5,
        category: str = "general",
        language: str = "en",
        time_range: str = "",
    ) -> str:
        """Search the live web and return ranked results with titles, URLs and snippets.

        Args:
            query: The search query. Be specific and use quotes for exact phrases.
            limit: Number of results to return (1-20).
            category: One of general, web, news, wiki, code, discussions.
            language: Language code, e.g. 'en', 'fr', 'de'.
            time_range: Optional freshness filter: day, week, month or year.
        """
        settings = get_settings()
        response = await execute_search(
            SearchRequest(
                query=query,
                category=category,
                limit=min(max(limit, 1), 20),
                language=language,
                time_range=time_range,
                format="markdown",
            ),
            get_client(),
            settings,
        )
        return format_results(response, "markdown")

    @mcp.tool()
    async def fetch_url(url: str, max_chars: int = 8000) -> str:
        """Fetch a web page and return its main readable content as Markdown.

        Args:
            url: A full http(s) URL, usually one returned by web_search.
            max_chars: Maximum number of characters to return.
        """
        settings = get_settings()
        data = await extract_url(url, get_client(), settings, max_chars=max_chars)
        return json.dumps(data, ensure_ascii=False, indent=2)

    @mcp.tool()
    async def list_sources() -> str:
        """List the search providers currently enabled on this SearNXG server."""
        settings = get_settings()
        lines = ["Enabled search sources:"]
        for name, enabled in settings.providers.items():
            detail = ""
            if name == "searxng" and settings.searxng_url:
                detail = f" ({settings.searxng_url})"
            lines.append(f"- {name}: {'enabled' if enabled else 'disabled'}{detail}")
        if settings.enable_extract:
            lines.append("- fetch_url: enabled")
        return "\n".join(lines)

    return mcp
