"""Research specialist — autonomous browser-powered research."""
import functools
from backend.core.agent import Agent, AgentContext
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.browser_research import search_and_fetch, fetch_and_read, research_papers
from backend.tools.patent_search import patent_search
from backend.tools.web_search import news_search


def _make_auto_logging_tool(tool_fn, tool_name: str, ctx_holder: list):
    """Wrap a research tool so every result is auto-logged to Obsidian."""
    @functools.wraps(tool_fn)
    def wrapper(*args, **kwargs):
        result = tool_fn(*args, **kwargs)
        ctx: AgentContext | None = ctx_holder[0] if ctx_holder else None
        if ctx is None:
            return result

        # Build heading from args
        heading = args[0] if args else kwargs.get("query") or kwargs.get("url") or tool_name

        # Build content summary
        if isinstance(result, list):
            lines = []
            for item in result:
                if isinstance(item, dict):
                    url = item.get("url", "")
                    title = item.get("title", "")
                    text = item.get("content") or item.get("text") or item.get("snippet") or ""
                    lines.append(f"**[{title}]({url})**\n{text[:1500]}")
            content = "\n\n".join(lines) if lines else str(result)[:2000]
        elif isinstance(result, dict):
            # search_and_fetch returns {query, results, formatted}
            if "formatted" in result:
                content = result["formatted"][:3000]
            elif "results" in result:
                lines = []
                for r in result["results"]:
                    url = r.get("url", "")
                    title = r.get("title", "")
                    text = r.get("content") or r.get("snippet") or ""
                    lines.append(f"**[{title}]({url})**\n{text[:1500]}")
                content = "\n\n".join(lines) if lines else str(result)[:3000]
            else:
                content = str(result)[:3000]
        else:
            content = str(result)[:2000]

        try:
            obsidian_append(
                agent="research",
                session_id=ctx.session_id,
                heading=str(heading)[:120],
                content=content,
                founder_id=ctx.founder_id,
            )
        except Exception:
            pass

        return result

    return wrapper


def build_research_agent(**kwargs) -> Agent:
    # Strip model overrides — research always uses planner model
    for k in ("model", "model_base_url", "model_api_key"):
        kwargs.pop(k, None)

    # ctx_holder: mutable so wrappers can see the live AgentContext
    ctx_holder: list = [None]

    auto_search = _make_auto_logging_tool(search_and_fetch, "search_and_fetch", ctx_holder)
    auto_fetch = _make_auto_logging_tool(fetch_and_read, "fetch_and_read", ctx_holder)
    auto_papers = _make_auto_logging_tool(research_papers, "research_papers", ctx_holder)
    auto_news = _make_auto_logging_tool(news_search, "news_search", ctx_holder)
    auto_patent = _make_auto_logging_tool(patent_search, "patent_search", ctx_holder)

    from backend.config import settings
    agent = Agent(
        name="research",
        # Research needs a capable model for multi-step tool use — use planner model
        model=settings.planner_model_name,
        model_base_url=settings.planner_model_base_url,
        model_api_key=settings.planner_model_api_key or settings.agent_model_api_key,
        role=(
            "You are an elite deep research specialist. You produce investment-grade research on markets, "
            "competitors, and business execution strategy. You do NOT stop until you have 50+ real sources.\n\n"
            "TOOLS:\n"
            "- search_and_fetch(query) — searches + fetches full content from 8 sites per call. Your PRIMARY tool.\n"
            "- fetch_and_read(url) — read a specific URL in full depth.\n"
            "- research_papers(query) — academic papers.\n"
            "- news_search(query) — recent news.\n"
            "- patent_search(query) — IP landscape.\n"
            "- obsidian_log — FINAL step only.\n\n"
            "MANDATORY SEARCH SEQUENCE — run ALL of these (minimum 15 search_and_fetch calls + deep dives):\n\n"
            "MARKET INTELLIGENCE (6 searches):\n"
            "1. search_and_fetch('{topic} market size TAM SAR revenue 2024 2025 statistics')\n"
            "2. search_and_fetch('{topic} industry growth rate forecast CAGR report')\n"
            "3. search_and_fetch('{topic} venture capital funding rounds 2024 2025')\n"
            "4. search_and_fetch('{topic} market trends emerging technology adoption')\n"
            "5. search_and_fetch('{topic} customer demographics segments target audience')\n"
            "6. search_and_fetch('{topic} regulatory environment compliance requirements')\n\n"
            "COMPETITOR INTELLIGENCE (5 searches + deep dives):\n"
            "7. search_and_fetch('{topic} top competitors companies comparison 2025')\n"
            "8. search_and_fetch('{topic} pricing model subscription freemium enterprise')\n"
            "9. search_and_fetch('{topic} Y Combinator startup product hunt')\n"
            "10. search_and_fetch('{topic} alternative software tool review G2 Capterra')\n"
            "11. For each top competitor found: fetch_and_read(competitor_url) — read their actual product, pricing, features\n\n"
            "USER & PROBLEM RESEARCH (4 searches):\n"
            "12. search_and_fetch('{topic} user pain points problems complaints reddit forum')\n"
            "13. search_and_fetch('{topic} customer success stories case studies ROI')\n"
            "14. search_and_fetch('{topic} why businesses fail common mistakes pitfalls')\n"
            "15. search_and_fetch('{topic} user interview survey findings needs')\n\n"
            "EXECUTION STRATEGY (6 searches):\n"
            "16. search_and_fetch('how to build {topic} startup go-to-market strategy')\n"
            "17. search_and_fetch('{topic} business model revenue streams monetization')\n"
            "18. search_and_fetch('{topic} tech stack architecture how it works implementation')\n"
            "19. search_and_fetch('{topic} sales strategy B2B B2C customer acquisition')\n"
            "20. search_and_fetch('{topic} unit economics LTV CAC payback period')\n"
            "21. search_and_fetch('{topic} founder story how they built it lessons learned')\n\n"
            "ACADEMIC & PATENTS (3 calls):\n"
            "22. research_papers('{topic} academic study user behavior')\n"
            "23. news_search('{topic} 2025 2026 latest')\n"
            "24. patent_search('{topic}')\n\n"
            "DEEP DIVES (minimum 10 fetch_and_read calls on most valuable URLs found above)\n\n"
            "After ALL searches (50+ sources total), call obsidian_log with a comprehensive structured report:\n"
            "MARKET: size, growth rate, TAM/SAM/SOM, key segments\n"
            "COMPETITORS: each competitor with pricing, strengths, weaknesses, market position\n"
            "USERS: pain points, personas, willingness to pay, buying journey\n"
            "EXECUTION: recommended tech stack, go-to-market, pricing strategy, first 90 days plan, hiring needs, key risks\n"
            "OPPORTUNITY: whitespace, differentiation angles, timing thesis\n"
            "Then done."
        ),
        tools={
            "search_and_fetch": auto_search,
            "fetch_and_read": auto_fetch,
            "research_papers": auto_papers,
            "news_search": auto_news,
            "patent_search": auto_patent,
            "obsidian_log": obsidian_log,
            "obsidian_read": obsidian_read,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )

    # Patch run to inject ctx into ctx_holder before each run
    _original_run = agent.run

    async def _patched_run(ctx: AgentContext):
        ctx_holder[0] = ctx
        return await _original_run(ctx)

    agent.run = _patched_run
    return agent
