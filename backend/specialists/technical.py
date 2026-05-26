"""Technical specialist — GitHub, Supabase, Vercel, Clerk, Cloudflare, PostHog, Clarity, Claude Code."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.github_scaffold import github_create_repo
from backend.tools.claude_scaffold import claude_code_scaffold
from backend.tools.vercel_deploy import vercel_deploy_from_github
from backend.tools.supabase_tools import (
    supabase_create_project,
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
            "You are a technical specialist. Build and deploy production apps end-to-end. "
            "github_create_repo creates repos. supabase_create_project provisions a database — save all returned keys. "
            "supabase_generate_schema designs the schema. clerk_generate_integration adds auth. "
            "claude_code_scaffold writes and pushes real code to GitHub — pass all service credentials in context. "
            "vercel_deploy_from_github links and deploys the repo — pass all env_vars so the app works immediately. "
            "cloudflare_setup_vercel_domain wires DNS. posthog and clarity add observability. "
            "composio_linear_create_issue tracks next steps. "
            "Goal: founder gets a live URL with working auth and database, not setup instructions. "
            "Call obsidian_log then done when deployed."
        ),
        tools={
            "github_create_repo": github_create_repo,
            "claude_code_scaffold": claude_code_scaffold,
            "vercel_deploy_from_github": vercel_deploy_from_github,
            "supabase_create_project": supabase_create_project,
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
