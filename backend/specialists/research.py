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
            "You are a deep research specialist. You conduct thorough, multi-angle research on any topic. "
            "Tools:\n"
            "- search_and_fetch(query) — PRIMARY TOOL. Searches and fetches full page content from 8 sites. Always use this first.\n"
            "- fetch_and_read(url) — read any specific URL directly (use to go deeper on a promising source).\n"
            "- research_papers(query) — academic papers and studies.\n"
            "- news_search(query) — recent news and developments.\n"
            "- patent_search(query) — IP landscape.\n"
            "- obsidian_log — FINAL step: log summary.\n\n"
            "Research tools auto-log every result to Obsidian — you do NOT need to call obsidian_append.\n\n"
            "REQUIRED: Run AT LEAST 8 searches covering ALL of:\n"
            "1. '{topic} market size revenue growth statistics'\n"
            "2. '{topic} competitors comparison pricing'\n"
            "3. '{topic} user reviews pain points problems'\n"
            "4. '{topic} startups funding venture capital'\n"
            "5. '{topic} technology how it works'\n"
            "6. research_papers('{topic} research study')\n"
            "7. news_search('{topic} 2025 2026')\n"
            "8. patent_search('{topic}')\n"
            "9+ Dive deeper into promising companies/papers with fetch_and_read(url).\n\n"
            "After all searches, call obsidian_log with a detailed structured summary covering: "
            "market size, top competitors with pricing, key user pain points, technology landscape, "
            "recent news, academic findings, patent activity. Then done."
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
