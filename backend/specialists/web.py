"""Web specialist — landing page, Vercel deploy, Cloudflare DNS, PostHog, Clarity."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.vercel_deploy import vercel_deploy, vercel_deploy_from_github, generate_landing_page_html
from backend.tools.github_scaffold import github_create_repo
from backend.tools.web_search import web_search
from backend.tools.cloudflare_tools import cloudflare_setup_vercel_domain, cloudflare_generate_instructions
from backend.tools.posthog_tools import posthog_generate_integration
from backend.tools.clarity_tools import clarity_generate_integration


def build_web_agent(**kwargs) -> Agent:
    return Agent(
        name="web",
        role=(
            "You are a web specialist. Build and deploy landing pages and web apps. "
            "generate_landing_page_html creates HTML with compelling copy. "
            "vercel_deploy deploys HTML directly; vercel_deploy_from_github deploys from a repo. "
            "github_create_repo creates repos. cloudflare_setup_vercel_domain wires DNS. "
            "posthog_generate_integration and clarity_generate_integration add analytics. "
            "Use research from shared context — don't re-search unless missing info. "
            "Call obsidian_log then done when deployed."
        ),
        tools={
            "generate_landing_page_html": generate_landing_page_html,
            "vercel_deploy": vercel_deploy,
            "vercel_deploy_from_github": vercel_deploy_from_github,
            "github_create_repo": github_create_repo,
            "web_search": web_search,
            "cloudflare_setup_vercel_domain": cloudflare_setup_vercel_domain,
            "cloudflare_generate_instructions": cloudflare_generate_instructions,
            "posthog_generate_integration": posthog_generate_integration,
            "clarity_generate_integration": clarity_generate_integration,
            "obsidian_log": obsidian_log,
            "obsidian_read": obsidian_read,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
