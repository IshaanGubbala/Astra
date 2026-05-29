"""Web specialist — generates HTML/CSS landing page and deploys to Vercel."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.vercel_deploy import vercel_deploy, generate_landing_page_html


def build_web_agent(**kwargs) -> Agent:
    # Wrap obsidian_read so it can only fire once per agent run
    _obsidian_read_done = {"done": False}

    def _obsidian_read_once(**kw):
        if _obsidian_read_done["done"]:
            return {"notes": [], "_blocked": "obsidian_read already called — proceed to generate_landing_page_html NOW"}
        _obsidian_read_done["done"] = True
        return obsidian_read(**kw)

    return Agent(
        name="web",
        role=(
            "You are a web specialist. Generate a high-quality HTML landing page and deploy it to Vercel.\n"
            "COMPANY_NAME is in SHARED CONTEXT — use it as the brand/product name everywhere.\n\n"
            "WORKFLOW — follow in strict order, no repetition:\n"
            "1. obsidian_read(agent='design') — fires ONCE. Extract colors/fonts/brand_vibe if present.\n"
            "   Whether notes have design context or not, immediately move to step 2.\n"
            "2. generate_landing_page_html(\n"
            "     page_title=<company name>,\n"
            "     headline=<sharp 6-10 word headline>,\n"
            "     subheadline=<one sentence value prop>,\n"
            "     value_props=<list of 4-6 specific feature/benefit strings>,\n"
            "     cta_text=<action CTA>,\n"
            "     cta_url='#waitlist',\n"
            "     company_name=<company name>,\n"
            "     business_context=<2-3 sentence product summary + EXACT colors/fonts/brand_vibe from design spec>\n"
            "   )\n"
            "   If no design spec, invent a distinctive premium palette. Use SPECIFIC copy.\n"
            "3. vercel_deploy(project_slug=<company-slug-landing>, html=<html from step 2>)\n"
            "4. obsidian_log — log the live Vercel URL\n"
            "5. done — return {url: <live Vercel URL>}\n\n"
            "Do NOT use GitHub, Next.js, React, or any build step. HTML + CSS only."
        ),
        tools={
            "generate_landing_page_html": generate_landing_page_html,
            "vercel_deploy": vercel_deploy,
            "obsidian_log": obsidian_log,
            "obsidian_read": _obsidian_read_once,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
