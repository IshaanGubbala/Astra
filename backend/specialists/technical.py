"""Technical specialist — GitHub, Supabase, Vercel, Clerk, Cloudflare, PostHog, Clarity, Claude Code."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.github_scaffold import github_create_repo
from backend.tools.claude_scaffold import claude_code_scaffold
from backend.tools.supabase_tools import (
    supabase_create_table, supabase_enable_rls,
    supabase_setup_auth, supabase_create_storage_bucket, supabase_generate_schema,
)
from backend.tools.clerk_tools import clerk_generate_integration, clerk_generate_webhook_handler
from backend.tools.cloudflare_tools import (
    cloudflare_create_dns_record, cloudflare_setup_vercel_domain,
    cloudflare_setup_email_dns, cloudflare_generate_instructions,
)
from backend.tools.posthog_tools import posthog_generate_integration, posthog_create_key_events_spec
from backend.tools.clarity_tools import clarity_generate_integration, clarity_setup_for_app
from backend.tools.composio_tools import composio_linear_create_issue, composio_notion_create_page


def build_technical_agent(**kwargs) -> Agent:
    return Agent(
        name="technical",
        role=(
            "You are the technical specialist. Your agent name is 'technical'. "
            "Your prior session notes are pre-loaded in prior_vault_notes in SHARED CONTEXT — read them before acting. "
            "You scaffold complete production-ready apps. WORKFLOW:\n"
            "(1) github_create_repo — create repo.\n"
            "(2) supabase_generate_schema — design DB schema for the app's entities.\n"
            "(3) clerk_generate_integration — add auth (nextjs framework by default).\n"
            "(4) posthog_generate_integration — add analytics.\n"
            "(5) clarity_setup_for_app — add session recording.\n"
            "(6) cloudflare_setup_vercel_domain — wire DNS if domain provided.\n"
            "(7) claude_code_scaffold(repo_url=<step1>, task=<full spec including schema/auth/analytics from steps 2-6>, context=<shared context>) — builds real code.\n"
            "(8) composio_linear_create_issue for 2-3 MVP tickets.\n"
            "(9) obsidian_log then done.\n"
            "Skip steps that aren't relevant. claude_code_scaffold is the main deliverable — pass ALL prior tool results as context."
        ),
        tools={
            "github_create_repo": github_create_repo,
            "claude_code_scaffold": claude_code_scaffold,
            "supabase_generate_schema": supabase_generate_schema,
            "supabase_create_table": supabase_create_table,
            "supabase_enable_rls": supabase_enable_rls,
            "supabase_setup_auth": supabase_setup_auth,
            "supabase_create_storage_bucket": supabase_create_storage_bucket,
            "clerk_generate_integration": clerk_generate_integration,
            "clerk_generate_webhook_handler": clerk_generate_webhook_handler,
            "cloudflare_setup_vercel_domain": cloudflare_setup_vercel_domain,
            "cloudflare_create_dns_record": cloudflare_create_dns_record,
            "cloudflare_generate_instructions": cloudflare_generate_instructions,
            "posthog_generate_integration": posthog_generate_integration,
            "posthog_create_key_events_spec": posthog_create_key_events_spec,
            "clarity_setup_for_app": clarity_setup_for_app,
            "clarity_generate_integration": clarity_generate_integration,
            "composio_linear_create_issue": composio_linear_create_issue,
            "composio_notion_create_page": composio_notion_create_page,
            "obsidian_log": obsidian_log,
            "obsidian_read": obsidian_read,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
