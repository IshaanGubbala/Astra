import logging
from typing import Optional

logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = 8) -> dict:
    """Search the web. Returns {query, results: [{title, url, snippet}], formatted: str}."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
        results = [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in raw
        ]
        return {
            "query": query,
            "results": results,
            "formatted": _format_results(query, results),
        }
    except Exception as e:
        logger.error("web_search failed: %s", e)
        return {"query": query, "results": [], "error": str(e), "formatted": f"Search failed: {e}"}


def news_search(query: str, max_results: int = 5) -> dict:
    """Search recent news. Returns {query, results: [{title, url, snippet, date}], formatted: str}."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            raw = list(ddgs.news(query, max_results=max_results))
        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("body", ""),
                "date": r.get("date", ""),
            }
            for r in raw
        ]
        return {
            "query": query,
            "results": results,
            "formatted": _format_results(query, results, show_date=True),
        }
    except Exception as e:
        logger.error("news_search failed: %s", e)
        return {"query": query, "results": [], "error": str(e), "formatted": f"Search failed: {e}"}


def search_and_read(query: str, max_results: int = 3) -> dict:
    """Search the web AND fetch + read actual page content from top results. Deeper than web_search."""
    from backend.tools.page_fetcher import search_and_read as _sar
    return _sar(query=query, max_results=max_results)


def fetch_page(url: str) -> dict:
    """Fetch and read a specific URL. Returns clean readable text content, stripped of ads/nav/footer."""
    from backend.tools.page_fetcher import fetch_page as _fp
    return _fp(url=url)


def _format_results(query: str, results: list, show_date: bool = False) -> str:
    if not results:
        return f"No results for: {query}"
    lines = [f"Search: {query}\n"]
    for i, r in enumerate(results, 1):
        date = f" [{r['date']}]" if show_date and r.get("date") else ""
        lines.append(f"{i}. {r['title']}{date}")
        lines.append(f"   {r['url']}")
        if r.get("snippet"):
            lines.append(f"   {r['snippet'][:200]}")
        lines.append("")
    return "\n".join(lines)
