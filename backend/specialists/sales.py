"""Sales specialist — lead discovery, outreach sequences, CRM tracking."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.lead_finder import find_leads, enrich_lead, build_outreach_sequence
from backend.tools.browser_research import search_and_fetch, fetch_and_read
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
            "You are a sales specialist. Find real leads and build outreach sequences.\n\n"
            "STEP 1 — Read context:\n"
            "obsidian_read(agent='research_competitors', founder_id=<FOUNDER_ID>) — get named competitors and target audience.\n"
            "obsidian_read(agent='research', founder_id=<FOUNDER_ID>) — get target customer segments.\n\n"
            "STEP 2 — Find leads using WORKING sources (NOT Reddit — blocked):\n"
            "a) search_and_fetch('site:producthunt.com <product_category> makers') — Product Hunt makers\n"
            "b) search_and_fetch('site:indiehackers.com <product_category> founder') — Indie Hackers founders\n"
            "c) search_and_fetch('site:news.ycombinator.com show HN <product_category>') — HN submissions\n"
            "d) search_and_fetch('<target_customer_type> <pain_point> contact email') — direct search\n"
            "e) fetch_and_read(<producthunt_page_url>) — extract maker names and profiles\n"
            "f) find_leads(industry=<niche>, job_title=<target_role>) — structured search\n\n"
            "STEP 3 — For each lead found:\n"
            "enrich_lead(company_name=<name>, website=<url>)\n"
            "build_outreach_sequence(lead=<enriched>, product_context=<your_product>)\n"
            "build_crm_contact(lead=<enriched>)\n\n"
            "STEP 4 — Email deliverability:\n"
            "create_warming_schedule() and generate_spf_dkim_instructions().\n\n"
            "STEP 5 — obsidian_log: LEADS FOUND, SEQUENCES BUILT, DELIVERABILITY SETUP.\n\n"
            "If all sources return 0 leads, build sequences targeting competitor customers "
            "using a '<competitor> alternative' angle from the research notes.\n\n"
            "Your final done output MUST include: leads (array), sequences (array), "
            "sequence (primary sequence array), and crm_contacts (array) for preview compatibility."
        ),
        tools={
            "search_and_fetch": search_and_fetch,
            "fetch_and_read": fetch_and_read,
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
