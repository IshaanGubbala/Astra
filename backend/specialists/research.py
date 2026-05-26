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
                    text = item.get("content") or item.get("text") or ""
                    lines.append(f"**[{title}]({url})**\n{text[:600]}")
            content = "\n\n".join(lines) if lines else str(result)[:800]
        elif isinstance(result, dict):
            content = str(result)[:800]
        else:
            content = str(result)[:800]

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
            "You are a research specialist. Browse the real web autonomously — full page content, "
            "research papers, news, and patents. Tools:\n"
            "- search_and_fetch(query) — search + read full content from real pages. Primary tool.\n"
            "- fetch_and_read(url) — read any URL directly.\n"
            "- research_papers(query) — academic papers and studies.\n"
            "- news_search(query) — recent news.\n"
            "- patent_search(query) — IP landscape.\n"
            "- obsidian_log — final session summary.\n\n"
            "Research tools auto-log every result to Obsidian — you do NOT need to call obsidian_append. "
            "Run 5-8 searches covering: market size, competitors, pricing, user pain points, "
            "recent news, academic research, patents. Then call obsidian_log with a summary and done."
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
