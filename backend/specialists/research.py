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
            "After EVERY search or page read, immediately call obsidian_append(agent='research', "
            "session_id=<SESSION from context>, heading=<query or topic>, content=<key facts found>, "
            "founder_id=<FOUNDER_ID from context>). Do not wait until the end — append after each tool call. "
            "Keep searching until coverage is comprehensive, then call obsidian_log then done."
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
