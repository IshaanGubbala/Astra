"""
Tool registry. Maps tool names to sync callables.
All tools must be sync (AstraAgent wraps execution in asyncio.to_thread).
"""
from backend.tools.web_search import web_search, news_search
from backend.tools.patent_search import patent_search
from backend.tools.vercel_deploy import vercel_deploy, generate_landing_page_html
from backend.tools.github_scaffold import github_create_repo
from backend.tools.social_content import generate_reel_package, generate_tiktok_package, generate_meta_ad
from backend.tools.email_campaign import send_email_campaign, build_email_html
from backend.tools.pdf_generator import generate_pdf
from backend.tools.doc_generator import format_legal_document
from backend.tools.composio_tools import (
    composio_gmail_send,
    composio_linkedin_post,
    composio_github_create_pr,
    composio_github_create_issue,
    composio_linear_create_issue,
    composio_calendar_create_event,
    composio_notion_create_page,
)
from backend.tools.company_brain import (
    add_company_brain_record,
    ask_company_brain,
    company_brain_agent_context,
    configure_company_brain_sync,
    get_company_brain_sync_status,
    ingest_company_brain_records,
    run_due_company_brain_syncs,
    maintain_company_brain,
    run_company_brain_sync,
    search_company_brain,
    sync_company_brain,
)
from backend.tools.company_brain_connectors import import_company_brain_source, import_company_brain_sources

TOOL_REGISTRY: dict[str, callable] = {
    # Research
    "web_search": web_search,
    "news_search": news_search,
    "patent_search": patent_search,

    # Web
    "vercel_deploy": vercel_deploy,
    "generate_landing_page_html": generate_landing_page_html,

    # Technical
    "github_create_repo": github_create_repo,

    # Marketing
    "generate_reel_package": generate_reel_package,
    "generate_tiktok_package": generate_tiktok_package,
    "generate_meta_ad": generate_meta_ad,
    "send_email_campaign": send_email_campaign,
    "build_email_html": build_email_html,

    # Legal / docs
    "generate_pdf": generate_pdf,
    "format_legal_document": format_legal_document,

    # Composio — OAuth-backed (Gmail, LinkedIn, GitHub PR, Linear, Calendar, Notion)
    "composio_gmail_send": composio_gmail_send,
    "composio_linkedin_post": composio_linkedin_post,
    "composio_github_create_pr": composio_github_create_pr,
    "composio_github_create_issue": composio_github_create_issue,
    "composio_linear_create_issue": composio_linear_create_issue,
    "composio_calendar_create_event": composio_calendar_create_event,
    "composio_notion_create_page": composio_notion_create_page,

    # Company brain — normalized cross-tool context for humans and agents
    "company_brain_search": search_company_brain,
    "company_brain_sync": sync_company_brain,
    "company_brain_add_record": add_company_brain_record,
    "company_brain_ingest_records": ingest_company_brain_records,
    "company_brain_maintain": maintain_company_brain,
    "company_brain_agent_context": company_brain_agent_context,
    "company_brain_ask": ask_company_brain,
    "company_brain_configure_sync": configure_company_brain_sync,
    "company_brain_sync_status": get_company_brain_sync_status,
    "company_brain_run_sync": run_company_brain_sync,
    "company_brain_run_due_syncs": run_due_company_brain_syncs,
    "company_brain_import_source": import_company_brain_source,
    "company_brain_import_sources": import_company_brain_sources,
}


def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Execute a registered tool. Returns result dict."""
    fn = TOOL_REGISTRY.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool '{tool_name}'. Available: {list(TOOL_REGISTRY.keys())}"}
    try:
        result = fn(**tool_input)
        return result if isinstance(result, dict) else {"result": result}
    except TypeError as e:
        return {"error": f"Tool '{tool_name}' called with wrong args: {e}"}
    except Exception as e:
        return {"error": f"Tool '{tool_name}' execution failed: {e}"}
