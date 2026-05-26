"""Research specialist — web search, news, patent search."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.web_search import web_search, news_search, search_and_read, fetch_page
from backend.tools.patent_search import patent_search


def build_research_agent(**kwargs) -> Agent:
    return Agent(
        name="research",
        role=(
            "You are a research specialist. Search broadly, read sources deeply, and synthesize findings. "
            "Use search_and_read for thorough source reading, web_search for quick broad queries, "
            "fetch_page for specific URLs, news_search for recent developments, patent_search for IP landscape. "
            "After EVERY tool call (web_search, search_and_read, fetch_page, news_search, patent_search), "
            "you MUST immediately call obsidian_append with:\n"
            "  agent='research'\n"
            "  session_id=<SESSION from context>\n"
            "  founder_id=<FOUNDER_ID from context>\n"
            "  heading=<the query or URL you just searched/fetched>\n"
            "  content=<for each result: URL + title + key facts/numbers extracted from that page, "
            "verbatim quotes where relevant. Do not summarize away the data — preserve URLs and specifics.>\n"
            "Never batch multiple searches before appending. One search → one immediate obsidian_append. "
            "Keep searching until comprehensive, then call obsidian_log then done."
        ),
        tools={
            "web_search": web_search,
            "search_and_read": search_and_read,
            "fetch_page": fetch_page,
            "news_search": news_search,
            "patent_search": patent_search,
            "obsidian_log": obsidian_log,
            "obsidian_read": obsidian_read,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
