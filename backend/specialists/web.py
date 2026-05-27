"""Web specialist — builds landing page via Claude Code, deploys to Vercel."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.github_scaffold import github_create_repo
from backend.tools.git_tools import run_claude_in_repo, write_files_to_repo
from backend.tools.vercel_deploy import vercel_deploy, vercel_deploy_from_github
from backend.tools.cloudflare_tools import cloudflare_setup_vercel_domain, cloudflare_generate_instructions
from backend.tools.posthog_tools import posthog_generate_integration
from backend.tools.clarity_tools import clarity_generate_integration


def build_web_agent(**kwargs) -> Agent:
    return Agent(
        name="web",
        role=(
            "You are a web specialist. Build a production-quality landing page and deploy it.\n\n"
            "WORKFLOW:\n"
            "1. obsidian_read(agent='web', founder_id=<FOUNDER_ID>) — get product/research context\n"
            "2. github_create_repo(repo_name=<company-landing>, description=<desc>)\n"
            "3. run_claude_in_repo(repo_url=<url>, session_id=<SESSION>, context=<research>, task=\n"
            "   'Build a complete Next.js 14 landing page for <product>. "
            "Single-page marketing site with: sticky nav, hero section, features grid, "
            "how-it-works steps, social proof/stats, final CTA, footer. "
            "Use Tailwind CSS. Dark theme (#06080f background, #3b82f6 accent). "
            "All copy must be specific to the product — real headlines, real value props, real feature names. "
            "Include package.json, next.config.js (NOT next.config.ts — use .js only), tailwind.config.js, app/layout.tsx, app/page.tsx, app/globals.css. "
            "After writing all files run: bash -c \"git add -A && git commit -m feat: landing page\"')\n"
            "4. vercel_deploy_from_github(repo_url=<url>)\n"
            "   - If deployed=True: proceed to step 5.\n"
            "   - If deployed=False: read the error field. Call run_claude_in_repo again with task='Fix this Vercel build error and commit: <paste error>'. "
            "Then call vercel_deploy_from_github again. Repeat this fix→redeploy loop up to 4 times until deployed=True. "
            "NEVER give up and log repo_url as the result — keep iterating until Vercel returns a live URL.\n"
            "5. obsidian_log — log repo_url and the live Vercel deploy URL\n"
            "6. done — return {repo_url, url} where url is the live Vercel URL\n\n"
            "Do NOT use generate_landing_page_html or vercel_deploy (HTML upload). "
            "Always build via GitHub repo + Claude Code. "
            "A successful deploy (deployed=True with a URL) is the only acceptable outcome."
        ),
        tools={
            "github_create_repo": github_create_repo,
            "run_claude_in_repo": run_claude_in_repo,
            "write_files_to_repo": write_files_to_repo,
            "vercel_deploy_from_github": vercel_deploy_from_github,
            "vercel_deploy": vercel_deploy,
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
