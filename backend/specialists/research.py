"""Research specialist — web search, news, patent search."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.web_search import web_search, news_search, search_and_read, fetch_page
from backend.tools.patent_search import patent_search


def build_research_agent(**kwargs) -> Agent:
    return Agent(
        name="research",
        role=(
            "You are the research specialist. "
            "Tools available:\n"
            "- search_and_read(query) — search and read full page content. Primary tool.\n"
            "- web_search(query) — quick snippets for broad queries.\n"
            "- fetch_page(url) — read a specific URL in full.\n"
            "- news_search(query) — recent news and developments.\n"
            "- patent_search(query) — patent landscape.\n"
            "- obsidian_log(agent, session_id, summary, output) — log findings when done.\n"
            "Workflow: search broadly, read sources, dig into relevant URLs, cover all angles "
            "(market size, competitors, pricing, regulation, recent news). "
            "Use as many tool calls as needed. When findings are comprehensive, "
            "call obsidian_log then the done tool."
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
