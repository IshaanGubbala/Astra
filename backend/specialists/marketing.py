"""Marketing specialist — social content, email campaigns, ad copy."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.social_content import generate_reel_package, generate_tiktok_package, generate_meta_ad
from backend.tools.email_campaign import send_email_campaign, build_email_html
from backend.tools.composio_tools import (
    composio_gmail_send,
    composio_linkedin_post,
)


def build_marketing_agent(**kwargs) -> Agent:
    return Agent(
        name="marketing",
        role=(
            "You are a marketing specialist. Create social content, email campaigns, and ad copy. "
            "generate_reel_package creates Instagram Reels scripts. generate_tiktok_package creates TikTok content. "
            "generate_meta_ad creates paid ad copy. build_email_html builds email templates. "
            "send_email_campaign sends campaigns. composio_gmail_send sends individual emails. "
            "composio_linkedin_post posts to LinkedIn. "
            "Produce all content formats the task requires. Call obsidian_log then done."
        ),
        tools={
            "generate_reel_package": generate_reel_package,
            "generate_tiktok_package": generate_tiktok_package,
            "generate_meta_ad": generate_meta_ad,
            "build_email_html": build_email_html,
            "send_email_campaign": send_email_campaign,
            "composio_gmail_send": composio_gmail_send,
            "composio_linkedin_post": composio_linkedin_post,
            "obsidian_log": obsidian_log,
            "obsidian_read": obsidian_read,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
