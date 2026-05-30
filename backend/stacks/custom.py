"""Custom stack package builder.

Allows founders to hand-pick a subset of the 6 specialist agents and receive
a deployable package — manifest, tasks, approval queue, and start payload —
scoped only to those agents.
"""
from __future__ import annotations

from typing import Any

from backend.stacks.catalog import VALID_AGENT_IDS, get_agent_entry
from backend.stacks.templates import (
    AgentStackTemplate,
    StackApprovalGate,
    StackArtifact,
    StackConnectorRequirement,
    StackTaskTemplate,
)

# ── Per-agent task templates (trimmed from IDEA_TO_REVENUE_STACK) ─────────────

_AGENT_TASKS: dict[str, StackTaskTemplate] = {
    "research": StackTaskTemplate(
        id="c_research",
        agent="research",
        title="Market and customer research",
        instruction=(
            "Validate the market, target customer, pain severity, buying trigger, "
            "category, pricing references, and early wedge. Produce specific research "
            "that downstream agents can use directly."
        ),
        depends_on=[],
        artifacts=["market_brief", "icp_brief", "pricing_hypothesis"],
    ),
    "legal": StackTaskTemplate(
        id="c_legal",
        agent="legal",
        title="Legal starter kit",
        instruction=(
            "Draft the legal and compliance starter kit appropriate for this outcome: "
            "privacy policy outline, terms outline, risk notes, entity considerations, "
            "and founder checklist. Do not file or publish anything without approval."
        ),
        depends_on=["c_research"],
        artifacts=["legal_checklist", "policy_outline"],
    ),
    "web": StackTaskTemplate(
        id="c_web",
        agent="web",
        title="Launch surface",
        instruction=(
            "Create and deploy a conversion-focused landing page based on the research. "
            "Include hero copy, value props, social proof framing, "
            "waitlist or lead capture direction, and deployment handoff."
        ),
        depends_on=["c_research"],
        artifacts=["landing_page", "website_copy"],
    ),
    "marketing": StackTaskTemplate(
        id="c_marketing",
        agent="marketing",
        title="Go-to-market motion",
        instruction=(
            "Create the launch marketing motion: positioning angle, first channels, "
            "content ideas, launch sequence, landing page CTA strategy, and messaging "
            "tests tied to the target customer."
        ),
        depends_on=["c_research"],
        artifacts=["gtm_plan", "launch_content"],
    ),
    "technical": StackTaskTemplate(
        id="c_technical",
        agent="technical",
        title="Product roadmap",
        instruction=(
            "Define the MVP product architecture and build path. Produce a practical "
            "technical roadmap with core entities, auth/data needs, repo structure, and "
            "first usable product scope."
        ),
        depends_on=["c_research"],
        artifacts=["mvp_roadmap", "technical_plan"],
    ),
    "ops": StackTaskTemplate(
        id="c_ops",
        agent="ops",
        title="Execution operating plan",
        instruction=(
            "Synthesize every completed lane into a founder operating plan: 30-day "
            "execution plan, weekly milestones, priorities, decision log, investor memo "
            "outline, and next actions for the founder."
        ),
        depends_on=["c_research", "c_legal", "c_web", "c_marketing", "c_technical"],
        artifacts=["thirty_day_plan", "investor_memo", "founder_next_actions"],
    ),
}

# Artifacts that each agent can produce (used to populate the artifact list)
_AGENT_ARTIFACTS: dict[str, list[StackArtifact]] = {
    "research": [
        StackArtifact("market_brief", "Market brief", "research", "Market size, category, trends, and validation signals."),
        StackArtifact("icp_brief", "ICP brief", "research", "Target customer, pain, trigger, objections, and buying process."),
        StackArtifact("pricing_hypothesis", "Pricing hypothesis", "research", "Initial packaging and pricing rationale."),
    ],
    "legal": [
        StackArtifact("legal_checklist", "Legal checklist", "legal", "Founder legal risk and setup checklist."),
        StackArtifact("policy_outline", "Policy outline", "legal", "Privacy and terms outline for launch."),
    ],
    "web": [
        StackArtifact("landing_page", "Landing page", "web", "Public launch surface or deployable page output."),
        StackArtifact("website_copy", "Website copy", "web", "Hero, sections, CTA, FAQ, and conversion copy."),
    ],
    "marketing": [
        StackArtifact("gtm_plan", "GTM plan", "marketing", "Launch channels, messaging tests, and initial campaign plan."),
        StackArtifact("launch_content", "Launch content", "marketing", "Social, email, and community copy drafts."),
    ],
    "technical": [
        StackArtifact("mvp_roadmap", "MVP roadmap", "technical", "Product scope, user stories, and build sequence."),
        StackArtifact("technical_plan", "Technical plan", "technical", "Architecture, data model, repo, and deployment plan."),
    ],
    "ops": [
        StackArtifact("thirty_day_plan", "30-day plan", "ops", "Week-by-week operating plan."),
        StackArtifact("investor_memo", "Investor memo", "ops", "Concise investor/fundraising narrative."),
        StackArtifact("founder_next_actions", "Founder next actions", "ops", "Prioritized next actions and approvals."),
    ],
}

# Approval gates that apply when a given agent is selected
_AGENT_APPROVAL_GATES: dict[str, StackApprovalGate] = {
    "web": StackApprovalGate(
        key="public_deploy",
        title="Publish public launch surface",
        trigger="web agent has a deployable landing page",
        required_before="public website publication or production domain changes",
        reason="Public-facing brand and claims need founder approval.",
    ),
    "marketing": StackApprovalGate(
        key="outbound_send",
        title="Send outbound email",
        trigger="marketing creates an email sequence",
        required_before="sending email to prospects or importing contacts into a campaign",
        reason="Outbound can affect reputation, deliverability, and legal compliance.",
    ),
    "legal": StackApprovalGate(
        key="legal_publish",
        title="Use legal documents publicly",
        trigger="legal agent drafts policy, terms, or entity guidance",
        required_before="publishing policies, filing entity documents, or paying filing fees",
        reason="Legal and financial actions must stay founder-controlled.",
    ),
}

# Connector requirements per agent
_AGENT_CONNECTORS: dict[str, list[StackConnectorRequirement]] = {
    "research": [],
    "legal": [
        StackConnectorRequirement("google_drive", "Google Drive", "knowledge", "Store legal and planning artifacts.", False),
    ],
    "web": [
        StackConnectorRequirement("github", "GitHub", "code", "Create or update the product repository.", True),
        StackConnectorRequirement("vercel", "Vercel", "deployment", "Deploy or prepare the launch surface.", True),
    ],
    "marketing": [
        StackConnectorRequirement("gmail", "Gmail", "outreach", "Draft founder-approved outbound and launch emails.", False),
    ],
    "technical": [
        StackConnectorRequirement("github", "GitHub", "code", "Create or update the product repository and preserve implementation handoff.", True),
        StackConnectorRequirement("vercel", "Vercel", "deployment", "Deploy or prepare the app preview.", True),
        StackConnectorRequirement("supabase", "Supabase", "data", "Prepare the database/auth foundation for the MVP.", False),
    ],
    "ops": [
        StackConnectorRequirement("google_drive", "Google Drive", "knowledge", "Store investor, legal, and planning artifacts.", False),
        StackConnectorRequirement("obsidian", "Obsidian", "company_brain", "Persist research, decisions, and execution context.", False),
    ],
}


def _prune_depends_on(task: StackTaskTemplate, selected_task_ids: set[str]) -> list[str]:
    """Remove dependency IDs that aren't in the selected set."""
    return [dep for dep in task.depends_on if dep in selected_task_ids]


def build_custom_stack_package(
    *,
    agents: list[str],
    instruction: str,
    founder_id: str = "",
    company_name: str | None = None,
) -> dict[str, Any]:
    """Build a deployable stack package for an arbitrary subset of agents."""
    # Validate agent IDs
    unknown = [a for a in agents if a not in VALID_AGENT_IDS]
    if unknown:
        return {
            "ok": False,
            "error": f"Unknown agent(s): {unknown}. Valid agents: {sorted(VALID_AGENT_IDS)}",
        }
    if not agents:
        return {"ok": False, "error": "agents list must contain at least one agent."}

    selected = list(dict.fromkeys(agents))  # deduplicate, preserve order

    # Build task list — prune deps to only selected tasks
    selected_task_ids = {_AGENT_TASKS[a].id for a in selected if a in _AGENT_TASKS}
    tasks: list[dict[str, Any]] = []
    for agent_id in selected:
        template = _AGENT_TASKS.get(agent_id)
        if not template:
            continue
        pruned_deps = _prune_depends_on(template, selected_task_ids)
        tasks.append({
            "id": template.id,
            "agent": template.agent,
            "instruction": (
                f"{template.instruction}\n\n"
                f"Founder goal: {instruction}\n\n"
                f"Stack: custom ({', '.join(selected)}). "
                f"Company: {company_name or 'unknown'}."
            ),
            "depends_on": pruned_deps,
            "stack_task_title": template.title,
            "expected_artifacts": list(template.artifacts),
        })

    # Build artifact list
    artifacts: list[dict[str, Any]] = []
    for agent_id in selected:
        for artifact in _AGENT_ARTIFACTS.get(agent_id, []):
            artifacts.append({
                "key": artifact.key,
                "title": artifact.title,
                "owner_agent": artifact.owner_agent,
                "description": artifact.description,
                "required": artifact.required,
            })

    # Build approval queue — only gates relevant to selected agents
    approval_queue: list[dict[str, Any]] = []
    seen_gate_keys: set[str] = set()
    for agent_id in selected:
        gate = _AGENT_APPROVAL_GATES.get(agent_id)
        if gate and gate.key not in seen_gate_keys:
            seen_gate_keys.add(gate.key)
            approval_queue.append({
                "key": gate.key,
                "title": gate.title,
                "trigger": gate.trigger,
                "required_before": gate.required_before,
                "reason": gate.reason,
                "status": "armed",
                "triggered_by": None,
            })

    # Build connector list (deduplicated by key, required wins)
    connectors_by_key: dict[str, dict[str, Any]] = {}
    for agent_id in selected:
        for req in _AGENT_CONNECTORS.get(agent_id, []):
            existing = connectors_by_key.get(req.key)
            if existing is None or (req.required and not existing["required"]):
                connectors_by_key[req.key] = {
                    "key": req.key,
                    "label": req.label,
                    "category": req.category,
                    "purpose": req.purpose,
                    "required": req.required,
                }
    required_connectors = [c for c in connectors_by_key.values() if c["required"]]
    optional_connectors = [c for c in connectors_by_key.values() if not c["required"]]

    # Agent catalog entries for selected agents
    agents_meta = [get_agent_entry(a) for a in selected if get_agent_entry(a)]

    return {
        "ok": True,
        "stack_id": "custom",
        "stack_name": f"Custom Stack ({', '.join(selected)})",
        "instruction": instruction,
        "founder_id": founder_id,
        "company_name": company_name or "",
        "agents": agents_meta,
        "tasks": tasks,
        "artifacts": artifacts,
        "approval_queue": approval_queue,
        "connector_setup": {
            "required": required_connectors,
            "optional": optional_connectors,
        },
        "start_payload": {
            "founder_id": founder_id or "<founder_id>",
            "instruction": instruction,
            "stack_id": "custom",
            "constraints": {
                "stack_id": "custom",
                "agents": selected,
                "company_name": company_name or "",
            },
        },
        "summary": (
            f"Custom stack with {len(selected)} agent(s) "
            f"({', '.join(selected)}), {len(tasks)} task(s), "
            f"{len(artifacts)} artifact(s), and {len(approval_queue)} approval gate(s)."
        ),
    }
