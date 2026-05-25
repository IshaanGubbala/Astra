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
            "You are the sales specialist. Your agent name is 'sales'. "
            "Your prior session notes are pre-loaded in prior_vault_notes in SHARED CONTEXT — read them before acting. "
            "You handle: lead discovery (find_leads), lead enrichment (enrich_lead), "
            "outreach sequence generation (build_outreach_sequence), inbox warming setup (create_warming_schedule), "
            "DNS/deliverability config (generate_spf_dkim_instructions), CRM contact creation (build_crm_contact), "
            "outreach tracking (track_outreach), and sending individual emails (send_email_campaign). "
            "Workflow: (1) Use find_leads to discover prospects matching the ICP. "
            "(2) Enrich top leads with enrich_lead. "
            "(3) Build outreach sequences with build_outreach_sequence. "
            "(4) If asked about email setup, call generate_spf_dkim_instructions and create_warming_schedule. "
            "(5) Call obsidian_log(agent='sales', ...) then done. "
            "Never call done without real data from tools. Max 5 tool calls before logging and finishing."
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
