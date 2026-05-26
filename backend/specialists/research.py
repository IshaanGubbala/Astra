"""Research specialist — autonomous browser-powered research."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.browser_research import search_and_fetch, fetch_and_read, research_papers
from backend.tools.patent_search import patent_search
from backend.tools.web_search import news_search


def build_research_agent(**kwargs) -> Agent:
    return Agent(
        name="research",
        role=(
            "You are a research specialist. You browse the real web autonomously — not just snippets, "
            "but full page content from actual sites, research papers, news, and patents. "
            "Tools:\n"
            "- search_and_fetch(query) — searches and reads full content from real pages. Primary tool.\n"
            "- fetch_and_read(url) — reads any specific URL directly (website, arXiv paper, news article, etc).\n"
            "- research_papers(query) — finds academic papers, studies, and research on a topic.\n"
            "- news_search(query) — recent news and developments.\n"
            "- patent_search(query) — IP landscape.\n"
            "- obsidian_append(...) — log findings mid-run.\n"
            "- obsidian_log(...) — final session log.\n\n"
            "After EVERY tool call, immediately call obsidian_append with:\n"
            "  agent='research', session_id=<SESSION>, founder_id=<FOUNDER_ID>,\n"
            "  heading=<query or URL>, content=<URL + title + extracted facts verbatim>.\n"
            "Never batch — one search → one immediate obsidian_append. "
            "Cover market size, competitors, pricing, user pain points, recent news, academic research, patents. "
            "When comprehensive, call obsidian_log then done."
        ),
        tools={
            "search_and_fetch": search_and_fetch,
            "fetch_and_read": fetch_and_read,
            "research_papers": research_papers,
            "news_search": news_search,
            "patent_search": patent_search,
            "obsidian_log": obsidian_log,
            "obsidian_read": obsidian_read,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
