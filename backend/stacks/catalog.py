"""Agent catalog — static metadata for every specialist agent in Astra.

Each entry describes the agent's identity, what tools it can use, what it
produces, and which agents must run before it (dependency graph).

Dependency graph:
  research  — no deps (runs first)
  web       — depends on research
  legal     — depends on research
  marketing — depends on research
  technical — depends on research
  ops       — depends on all five above
"""
from __future__ import annotations

from typing import Any

AGENT_CATALOG: list[dict[str, Any]] = [
    {
        "id": "research",
        "name": "Research",
        "description": (
            "Market sizing, competitor analysis, TAM/SAM/SOM, customer profile. "
            "Performs deep web, news, patent, and video research to validate markets "
            "and produce structured briefs downstream agents can use directly."
        ),
        "tools": [
            "search_and_fetch",
            "fetch_and_read",
            "research_papers",
            "news_search",
            "patent_search",
            "youtube_research",
            "tiktok_research",
            "obsidian_log",
            "obsidian_read",
            "obsidian_append",
        ],
        "produces": [
            "market_research_report",
            "competitor_analysis",
            "customer_personas",
            "market_brief",
            "icp_brief",
            "pricing_hypothesis",
        ],
        "depends_on": [],
    },
    {
        "id": "legal",
        "name": "Legal",
        "description": (
            "Privacy policies, terms of service, founder agreements, IP assignment, "
            "entity formation guidance, and patent landscape research. Generates "
            "PDF-ready legal documents and a founder compliance checklist."
        ),
        "tools": [
            "generate_pdf",
            "patent_search",
            "format_legal_document",
            "file_llc_live",
            "obsidian_log",
            "obsidian_read",
            "obsidian_append",
        ],
        "produces": [
            "legal_checklist",
            "policy_outline",
            "founder_agreement",
            "patent_landscape",
        ],
        "depends_on": ["research"],
    },
    {
        "id": "web",
        "name": "Web",
        "description": (
            "Landing page generation, Vercel deployment, conversion-focused copy, "
            "and website architecture. Builds and deploys a public-facing launch "
            "surface based on research and brand direction."
        ),
        "tools": [
            "generate_landing_page_html",
            "vercel_deploy",
            "obsidian_log",
            "obsidian_read",
            "obsidian_append",
        ],
        "produces": [
            "landing_page",
            "website_copy",
            "deployed_url",
        ],
        "depends_on": ["research"],
    },
    {
        "id": "marketing",
        "name": "Marketing",
        "description": (
            "Go-to-market strategy, social media content (Reels, TikTok, LinkedIn), "
            "Meta ad copy, email campaigns, and growth channel planning. Produces "
            "launch-ready creative assets and a sequenced GTM plan."
        ),
        "tools": [
            "search_and_fetch",
            "generate_reel_package",
            "generate_tiktok_package",
            "generate_meta_ad",
            "generate_ad_image",
            "build_email_html",
            "send_email_campaign",
            "composio_gmail_send",
            "composio_linkedin_post",
            "obsidian_log",
            "obsidian_read",
            "obsidian_append",
        ],
        "produces": [
            "gtm_plan",
            "launch_content",
            "ad_creatives",
            "email_sequence",
            "social_posts",
        ],
        "depends_on": ["research"],
    },
    {
        "id": "technical",
        "name": "Technical",
        "description": (
            "Software architecture, MVP development, GitHub repo creation, Vercel "
            "deployment, Supabase schema generation, Clerk auth integration, and "
            "full-stack implementation planning. Produces an actionable technical "
            "roadmap and working code skeleton."
        ),
        "tools": [
            "github_create_repo",
            "run_mvp_loop",
            "run_claude_in_repo",
            "write_files_to_repo",
            "vercel_deploy_from_github",
            "supabase_generate_schema",
            "supabase_create_project",
            "clerk_generate_integration",
            "posthog_generate_integration",
            "composio_linear_create_issue",
            "composio_notion_create_page",
            "create_product_with_payment_link",
            "obsidian_log",
            "obsidian_read",
            "obsidian_append",
        ],
        "produces": [
            "mvp_roadmap",
            "technical_plan",
            "github_repo",
            "deployed_app",
            "database_schema",
        ],
        "depends_on": ["research"],
    },
    {
        "id": "ops",
        "name": "Operations",
        "description": (
            "Synthesizes every agent lane into a founder operating plan: 30-day "
            "execution calendar, investor memo, weekly cadence, Notion/Linear "
            "project setup, and prioritized next actions. Runs last after all "
            "other agents complete."
        ),
        "tools": [
            "generate_pdf",
            "composio_gmail_send",
            "composio_calendar_create_event",
            "composio_notion_create_page",
            "composio_linear_create_issue",
            "resend_send_email",
            "resend_generate_integration",
            "resend_create_email_templates",
            "create_product_with_payment_link",
            "obsidian_log",
            "obsidian_read",
            "obsidian_append",
        ],
        "produces": [
            "thirty_day_plan",
            "investor_memo",
            "founder_next_actions",
            "operating_cadence",
            "decision_log",
        ],
        "depends_on": ["research", "legal", "web", "marketing", "technical"],
    },
]

# Fast lookup by id
_CATALOG_BY_ID: dict[str, dict[str, Any]] = {a["id"]: a for a in AGENT_CATALOG}

# Valid agent IDs for validation
VALID_AGENT_IDS: frozenset[str] = frozenset(_CATALOG_BY_ID)


def get_agent_catalog() -> list[dict[str, Any]]:
    """Return the full agent catalog."""
    return AGENT_CATALOG


def get_agent_entry(agent_id: str) -> dict[str, Any] | None:
    """Return a single agent catalog entry or None."""
    return _CATALOG_BY_ID.get(agent_id)
