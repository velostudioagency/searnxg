"""A tiny built-in reference library used only when every web source fails.

Results are clearly labelled as offline samples so they can never be mistaken
for live web results. This exists so the app is still useful on locked-down
networks, during outages, or before a SearXNG instance is configured.
"""

from __future__ import annotations

from .models import SearchResult

LIBRARY: list[dict[str, str]] = [
    {
        "title": "Python programming language - official site",
        "url": "https://www.python.org/",
        "content": "Python is a programming language that lets you work quickly and integrate systems more effectively. It has a large standard library and an active community.",
        "keywords": "python programming language learn code",
    },
    {
        "title": "Python documentation",
        "url": "https://docs.python.org/3/",
        "content": "The official Python documentation covering the language reference, tutorial, standard library and how-to guides.",
        "keywords": "python docs documentation reference tutorial",
    },
    {
        "title": "FastAPI - modern Python web framework",
        "url": "https://fastapi.tiangolo.com/",
        "content": "FastAPI is a Python web framework for building APIs based on standard Python type hints, with automatic interactive documentation.",
        "keywords": "fastapi python api framework rest",
    },
    {
        "title": "Model Context Protocol (MCP)",
        "url": "https://modelcontextprotocol.io/",
        "content": "MCP is an open protocol that standardises how applications provide context and tools to large language models.",
        "keywords": "mcp model context protocol ai tools agents",
    },
    {
        "title": "SearXNG - privacy-respecting metasearch engine",
        "url": "https://github.com/searxng/searxng",
        "content": "SearXNG is a free internet metasearch engine which aggregates results from many search services without tracking its users.",
        "keywords": "searxng search engine privacy metasearch self hosted",
    },
    {
        "title": "Docker documentation",
        "url": "https://docs.docker.com/",
        "content": "Docker documentation for building, running and shipping applications in containers.",
        "keywords": "docker containers compose deployment",
    },
    {
        "title": "React documentation",
        "url": "https://react.dev/",
        "content": "React is a JavaScript library for building user interfaces from components, with hooks for state and effects.",
        "keywords": "react javascript ui frontend components",
    },
    {
        "title": "Git documentation",
        "url": "https://git-scm.com/doc",
        "content": "Git is a distributed version control system for tracking changes in source code during software development.",
        "keywords": "git version control github repository",
    },
    {
        "title": "Linux documentation project",
        "url": "https://www.tldp.org/",
        "content": "Documentation and guides for the Linux operating system, covering administration, commands and shell usage.",
        "keywords": "linux shell bash server administration",
    },
    {
        "title": "PostgreSQL documentation",
        "url": "https://www.postgresql.org/docs/",
        "content": "PostgreSQL is a powerful open source relational database system with a strong reputation for reliability and correctness.",
        "keywords": "postgres postgresql database sql",
    },
    {
        "title": "FastAPI documentation: first steps",
        "url": "https://fastapi.tiangolo.com/tutorial/first-steps/",
        "content": "A step-by-step introduction to creating a small FastAPI application and running it with Uvicorn.",
        "keywords": "fastapi uvicorn tutorial api python",
    },
    {
        "title": "Model Context Protocol specification",
        "url": "https://spec.modelcontextprotocol.io/",
        "content": "The MCP specification describes servers, clients, tools, resources and prompts, and how they communicate.",
        "keywords": "mcp specification protocol tools servers clients",
    },
    {
        "title": "Web search basics",
        "url": "https://en.wikipedia.org/wiki/Web_search_engine",
        "content": "A web search engine searches the internet for information requested in a query and returns a list of results.",
        "keywords": "web search engine how search works internet",
    },
    {
        "title": "Privacy and search engines",
        "url": "https://en.wikipedia.org/wiki/SearX",
        "content": "Privacy-focused search engines avoid profiling users and do not build search histories tied to identities.",
        "keywords": "privacy search tracking metasearch searx",
    },
    {
        "title": "OpenAI API documentation",
        "url": "https://platform.openai.com/docs",
        "content": "Documentation for the OpenAI API, including chat completions, function calling and tool use.",
        "keywords": "openai api gpt function calling tools llm",
    },
    {
        "title": "JavaScript MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
        "content": "MDN reference for JavaScript, the programming language of the web, including guides and API documentation.",
        "keywords": "javascript js mdn web browser",
    },
    {
        "title": "Nginx documentation",
        "url": "https://nginx.org/en/docs/",
        "content": "Nginx is a web server that can also be used as a reverse proxy, load balancer and HTTP cache.",
        "keywords": "nginx web server reverse proxy",
    },
    {
        "title": "Github documentation",
        "url": "https://docs.github.com/",
        "content": "Guides for using GitHub repositories, issues, pull requests and actions to collaborate on software.",
        "keywords": "github repository pull request actions code",
    },
]


def offline_results(query: str, limit: int) -> list[SearchResult]:
    """Return clearly-labelled reference hits ranked by keyword overlap."""
    terms = [t.lower() for t in query.split() if len(t) > 2]
    scored: list[tuple[int, dict[str, str]]] = []
    for entry in LIBRARY:
        haystack = f"{entry['title']} {entry['content']} {entry['keywords']}".lower()
        score = sum(1 for term in terms if term in haystack)
        if score:
            scored.append((score, entry))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        SearchResult(
            title=entry["title"],
            url=entry["url"],
            content=f"Offline sample result. {entry['content']}",
            engine="Offline library",
            category="general",
            score=float(score),
        )
        for score, entry in scored[:limit]
    ]
