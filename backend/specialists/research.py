"""Research specialist — web search, deep page reading, news, patent search."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.web_search import web_search, news_search, search_and_read, fetch_page
from backend.tools.patent_search import patent_search


def build_research_agent(**kwargs) -> Agent:
    return Agent(
        name="research",
        role=(
            "You are the research specialist. Your agent name is 'research'. "
            "Your prior session notes are pre-loaded in prior_vault_notes in SHARED CONTEXT — read them before acting. "
            "Tools available: web_search (quick search, snippets only), search_and_read (search + fetch actual page content — use for deep research), "
            "fetch_page (read a specific URL in full), news_search (recent news), patent_search. "
            "Workflow: "
            "(1) Use search_and_read for your main research query — it fetches actual page content, not just snippets. "
            "(2) Use fetch_page to read specific competitor or data pages in full. "
            "(3) Use news_search for recent developments. "
            "(4) Max 3 tool calls total — you have deep content per call. "
            "(5) Call obsidian_log(agent='research', ...) then done. "
            "Never call done without tool results. Use search_and_read over web_search for quality research."
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
