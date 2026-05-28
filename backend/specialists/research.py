"""Research specialist — autonomous browser-powered research."""
import functools
from backend.core.agent import Agent, AgentContext
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.browser_research import search_and_fetch, fetch_and_read, research_papers
from backend.tools.patent_search import patent_search
from backend.tools.web_search import news_search, deep_research
from backend.tools.video_research import youtube_research, tiktok_research


def _make_auto_logging_tool(tool_fn, tool_name: str, ctx_holder: list, agent_name: str = "research"):
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
                agent=agent_name,
                session_id=ctx.session_id,
                heading=str(heading)[:120],
                content=content,
                founder_id=ctx.founder_id,
            )
        except Exception:
            pass

        return result

    return wrapper


_FOCUS_ROLES = {
    "research": (
        "MARKET INTELLIGENCE (run ALL 6):\n"
        "1. search_and_fetch('{topic} market size TAM revenue 2024 2025 statistics')\n"
        "2. search_and_fetch('{topic} industry growth rate forecast CAGR VC funding')\n"
        "3. search_and_fetch('{topic} market trends emerging technology adoption')\n"
        "4. search_and_fetch('{topic} customer demographics segments target audience')\n"
        "5. search_and_fetch('{topic} regulatory environment compliance requirements')\n"
        "6. news_search('{topic} 2025 2026 latest')\n\n"
        "Then 4 fetch_and_read calls on the highest-value URLs found.\n"
        "obsidian_log with: MARKET SIZE, TAM/SAM/SOM, KEY SEGMENTS, REGULATORY, VC FUNDING DATA."
    ),
    "research_2": (
        "MARKET DEEP DIVE (run ALL 5 — complement the market agent, don't duplicate):\n"
        "1. research_papers('{topic} academic study user behavior market')\n"
        "2. search_and_fetch('{topic} enterprise buyers procurement budget decision maker')\n"
        "3. search_and_fetch('{topic} failure modes risks challenges why startups fail')\n"
        "4. search_and_fetch('{topic} pricing benchmarks willingness to pay survey')\n"
        "5. deep_research('{topic} market size total addressable market statistics 2025')\n\n"
        "Then 3 fetch_and_read calls on the most data-rich URLs.\n"
        "obsidian_log with: BUYER PERSONAS, RISK FACTORS, PRICING BENCHMARKS, ACADEMIC FINDINGS."
    ),
    "research_competitors": (
        "COMPETITOR INTELLIGENCE (run ALL 10):\n"
        "1. deep_research('named companies and platforms in the {topic} space — list every startup and incumbent with funding')\n"
        "2. search_and_fetch('{topic} top companies startups list 2024 2025 crunchbase')\n"
        "3. search_and_fetch('{topic} Y Combinator a16z sequoia backed startup')\n"
        "4. search_and_fetch('{topic} alternatives competitors site:producthunt.com OR site:g2.com')\n"
        "5. search_and_fetch('{topic} pricing model subscription freemium enterprise')\n"
        "6. search_and_fetch('{topic} market map landscape 2024 2025')\n"
        "7. news_search('{topic} company startup launch funding 2024 2025')\n"
        "8. youtube_research('{topic} platform demo review walkthrough')\n"
        "9. patent_search('{topic}')\n"
        "10. search_and_fetch('{topic} customer reviews complaints weaknesses')\n\n"
        "CRITICAL: After step 1-4, you MUST have named companies. For EACH named competitor: fetch_and_read their homepage.\n"
        "obsidian_log with: COMPETITOR TABLE (name, URL, pricing, funding, strengths, weaknesses), WHITESPACE OPPORTUNITIES."
    ),
    "research_competitors_2": (
        "COMPETITOR DEEP DIVE (run ALL 5 — dig into top 3 competitors found by the other competitor agent):\n"
        "1. search_and_fetch('{topic} competitor comparison head to head strengths weaknesses')\n"
        "2. tiktok_research('{topic} competitor review product')\n"
        "3. search_and_fetch('{topic} user switching from competitor complaints reddit')\n"
        "4. search_and_fetch('{topic} competitor acquisition acqui-hire M&A exit')\n"
        "5. search_and_fetch('{topic} white label reseller partner program')\n\n"
        "Read obsidian_read for any competitor URLs already found, then fetch_and_read their pricing pages.\n"
        "obsidian_log with: COMPETITOR DEEP-DIVE, SWITCHING COSTS, USER PAIN POINTS WITH COMPETITORS, M&A ACTIVITY."
    ),
    "research_execution": (
        "EXECUTION STRATEGY RESEARCH (run ALL 8):\n"
        "1. search_and_fetch('how to build {topic} startup go-to-market strategy')\n"
        "2. search_and_fetch('{topic} business model revenue streams monetization')\n"
        "3. search_and_fetch('{topic} tech stack architecture implementation')\n"
        "4. search_and_fetch('{topic} unit economics LTV CAC payback period')\n"
        "5. search_and_fetch('{topic} user pain points problems complaints needs')\n"
        "6. search_and_fetch('{topic} founder story how they built it lessons learned')\n"
        "7. youtube_research('{topic} startup founder how to build')\n"
        "8. search_and_fetch('{topic} sales strategy B2B B2C customer acquisition')\n\n"
        "Then 4 fetch_and_read calls on the most actionable URLs.\n"
        "obsidian_log with: RECOMMENDED TECH STACK, GTM STRATEGY, PRICING MODEL, FIRST 90 DAYS PLAN, USER PERSONAS, KEY RISKS."
    ),
    "research_execution_2": (
        "EXECUTION DEEP DIVE (run ALL 5 — complement execution agent, no overlap):\n"
        "1. tiktok_research('{topic} startup tips growth hacks viral marketing')\n"
        "2. search_and_fetch('{topic} cold email outreach template founder sales')\n"
        "3. search_and_fetch('{topic} SEO content marketing strategy organic growth')\n"
        "4. search_and_fetch('{topic} investor pitch deck what VCs want to see')\n"
        "5. search_and_fetch('{topic} partnership channel distribution strategy')\n\n"
        "obsidian_log with: GROWTH PLAYBOOK, SALES TEMPLATES, CONTENT STRATEGY, INVESTOR ANGLES, CHANNEL STRATEGY."
    ),
}


def build_research_agent(agent_name: str = "research", **kwargs) -> Agent:
    # Strip model overrides — research always uses planner model
    for k in ("model", "model_base_url", "model_api_key"):
        kwargs.pop(k, None)

    # ctx_holder: mutable so wrappers can see the live AgentContext
    ctx_holder: list = [None]

    # _2 variants log to the same Obsidian note as their base so notes merge
    log_name = agent_name.removesuffix("_2")
    auto_search = _make_auto_logging_tool(search_and_fetch, "search_and_fetch", ctx_holder, log_name)
    auto_fetch = _make_auto_logging_tool(fetch_and_read, "fetch_and_read", ctx_holder, log_name)
    auto_papers = _make_auto_logging_tool(research_papers, "research_papers", ctx_holder, log_name)
    auto_news = _make_auto_logging_tool(news_search, "news_search", ctx_holder, log_name)
    auto_patent = _make_auto_logging_tool(patent_search, "patent_search", ctx_holder, log_name)
    auto_youtube = _make_auto_logging_tool(youtube_research, "youtube_research", ctx_holder, log_name)
    auto_tiktok = _make_auto_logging_tool(tiktok_research, "tiktok_research", ctx_holder, log_name)
    auto_deep = _make_auto_logging_tool(deep_research, "deep_research", ctx_holder, log_name)

    from backend.config import settings
    focus_searches = _FOCUS_ROLES.get(agent_name, _FOCUS_ROLES["research"])
    agent = Agent(
        name=agent_name,
        model=settings.planner_model_name,
        model_base_url=settings.planner_model_base_url,
        model_api_key=settings.planner_model_api_key or settings.agent_model_api_key,
        role=(
            "You are an elite deep research specialist. You produce investment-grade research. "
            "You do NOT stop until you have completed ALL mandatory searches below.\n\n"
            "TOOLS:\n"
            "- search_and_fetch(query) — searches + fetches full content from multiple sites. PRIMARY tool.\n"
            "- fetch_and_read(url) — read a specific URL in full depth.\n"
            "- research_papers(query) — academic papers.\n"
            "- news_search(query) — recent news.\n"
            "- patent_search(query) — IP landscape.\n"
            "- youtube_research(query) — YouTube video metadata + transcripts for competitor/creator analysis.\n"
            "- tiktok_research(query) — TikTok video metadata + captions for viral trend analysis.\n"
            "- deep_research(query) — Gemini + Google Search grounded research. Best for finding named companies, market maps, and entities.\n"
            "- obsidian_log — FINAL step only after ALL searches complete.\n\n"
            "YOUR MANDATORY SEARCH SEQUENCE (replace {topic} with the actual subject):\n\n"
            + focus_searches
        ),
        tools={
            "search_and_fetch": auto_search,
            "fetch_and_read": auto_fetch,
            "research_papers": auto_papers,
            "news_search": auto_news,
            "patent_search": auto_patent,
            "youtube_research": auto_youtube,
            "tiktok_research": auto_tiktok,
            "deep_research": auto_deep,
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
