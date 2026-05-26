"""Sales specialist — lead discovery, inbox warming, outbound sequences, CRM tracking."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.lead_finder import find_leads, enrich_lead, build_outreach_sequence
from backend.tools.inbox_warmer import (
    create_warming_schedule,
    generate_spf_dkim_instructions,
    build_crm_contact,
    track_outreach,
)
from backend.tools.email_campaign import send_email_campaign


def build_sales_agent(**kwargs) -> Agent:
    return Agent(
        name="sales",
        role=(
            "You are a sales specialist. Find leads, enrich them, and build outreach sequences. "
            "find_leads discovers prospects matching the ICP — pass no_website=True for offline businesses. "
            "enrich_lead gets contact details for specific leads. "
            "build_outreach_sequence creates personalized multi-touch email sequences. "
            "create_warming_schedule and generate_spf_dkim_instructions set up email deliverability. "
            "build_crm_contact and track_outreach manage the pipeline. "
            "send_email_campaign sends sequences. "
            "Call obsidian_log then done when you have real lead and sequence data."
        ),
        tools={
            "find_leads": find_leads,
            "enrich_lead": enrich_lead,
            "build_outreach_sequence": build_outreach_sequence,
            "create_warming_schedule": create_warming_schedule,
            "generate_spf_dkim_instructions": generate_spf_dkim_instructions,
            "build_crm_contact": build_crm_contact,
            "track_outreach": track_outreach,
            "send_email_campaign": send_email_campaign,
            "obsidian_log": obsidian_log,
            "obsidian_read": obsidian_read,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
