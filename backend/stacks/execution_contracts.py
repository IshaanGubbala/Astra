"""Production execution contracts for Agent Stacks.

Templates define the department shape. Execution contracts define how that
department should operate in production: milestones, KPIs, quality gates,
handoffs, recurring cadence, and what each lane must prove before completion.
"""

from __future__ import annotations

from typing import Any

from backend.stacks.templates import AgentStackTemplate, StackTaskTemplate


_STACK_CONTRACTS: dict[str, dict[str, Any]] = {
    "idea_to_revenue": {
        "north_star": "A founder can move from rough idea to a credible first launch with a public surface, operating plan, and outreach-ready assets.",
        "milestones": [
            {"day": 0, "title": "Company genome locked", "evidence": "Goal, customer hypothesis, constraints, and stack choice saved to Company Brain."},
            {"day": 3, "title": "Market truth established", "evidence": "Market brief, ICP, pricing hypothesis, and competitor wedge are complete."},
            {"day": 7, "title": "Launch surface ready", "evidence": "Landing page/copy, brand direction, and conversion path are ready for approval."},
            {"day": 14, "title": "Revenue motion ready", "evidence": "CRM fields, outbound sequence, sales script, and GTM plan are prepared."},
            {"day": 30, "title": "Founder execution system active", "evidence": "30-day plan, investor memo, legal checklist, and next actions are canonical."},
        ],
        "kpis": [
            {"key": "ready_artifacts", "label": "Required launch artifacts ready", "target": ">= 14"},
            {"key": "validated_icp", "label": "Specific ICP and pain statement", "target": "1 canonical ICP"},
            {"key": "launch_surface", "label": "Public launch surface prepared", "target": "deployable or explicitly blocked"},
            {"key": "founder_next_actions", "label": "Prioritized next actions", "target": ">= 10 concrete actions"},
        ],
        "quality_gates": [
            "Every output names the specific ICP, not a generic audience.",
            "Public claims are clearly separated from internal hypotheses.",
            "Outreach and legal/publication actions remain approval-gated.",
            "Ops must synthesize cross-lane contradictions before final handoff.",
        ],
    },
    "sales": {
        "north_star": "A team can run a weekly sales motion with clear ICP, CRM state, approved outbound, and measurable pipeline progress.",
        "milestones": [
            {"day": 0, "title": "Revenue target and buyer hypothesis", "evidence": "Target buyer, offer, ACV, and constraints are known."},
            {"day": 2, "title": "Lead and CRM system", "evidence": "Lead criteria, CRM stages, fields, and qualification model are defined."},
            {"day": 5, "title": "Outbound approved", "evidence": "Sequence variants and founder approval checklist are ready."},
            {"day": 7, "title": "Pipeline rhythm live", "evidence": "Weekly review, metrics, and follow-up cadence are active."},
        ],
        "kpis": [
            {"key": "qualified_segments", "label": "Qualified buyer segments", "target": ">= 2"},
            {"key": "sequence_variants", "label": "Outbound variants", "target": ">= 3"},
            {"key": "crm_fields", "label": "CRM fields/stages", "target": "complete handoff"},
            {"key": "approval_state", "label": "Outbound approval", "target": "approved or queued"},
        ],
        "quality_gates": [
            "Lead sources must include rationale and disqualification rules.",
            "Outbound must include compliance/reputation notes.",
            "CRM stages must have exit criteria and next actions.",
            "No live sending occurs without approval.",
        ],
    },
    "marketing": {
        "north_star": "A campaign can launch with positioning, channel strategy, creative briefs, conversion copy, and measurement.",
        "milestones": [
            {"day": 0, "title": "Audience and channel truth", "evidence": "Audience brief and channel map complete."},
            {"day": 3, "title": "Creative system", "evidence": "Visual direction and campaign creative rules complete."},
            {"day": 5, "title": "Campaign package", "evidence": "Campaign plan, calendar, copy, and briefs complete."},
            {"day": 7, "title": "Measurement and optimization loop", "evidence": "KPIs, dashboard spec, and post-launch loop complete."},
        ],
        "kpis": [
            {"key": "channel_fit", "label": "Primary channels justified", "target": ">= 2 channels"},
            {"key": "campaign_assets", "label": "Campaign-ready assets", "target": ">= 8 assets/briefs"},
            {"key": "measurement_plan", "label": "Measurement plan", "target": "traffic + conversion + learning metrics"},
            {"key": "approval_state", "label": "Public campaign approval", "target": "approved or queued"},
        ],
        "quality_gates": [
            "Campaign claims must map to evidence or be flagged as hypotheses.",
            "Each channel must have a clear CTA and measurement event.",
            "Paid spend requires explicit approval.",
            "Creative guidance must be specific enough for asset production.",
        ],
    },
    "founder_ops": {
        "north_star": "The founder has a weekly command center with decisions, risks, metrics, investor updates, and connector-backed memory.",
        "milestones": [
            {"day": 0, "title": "Company context normalized", "evidence": "Current priorities, deadlines, risks, and open questions are captured."},
            {"day": 2, "title": "Operating cadence designed", "evidence": "Weekly review, decision log, and owner map are defined."},
            {"day": 5, "title": "Investor/exec reporting ready", "evidence": "Investor update and metrics narrative are ready for founder approval."},
            {"day": 7, "title": "Command center connected", "evidence": "Docs/chat/calendar connector plan and Company Brain records are in place."},
        ],
        "kpis": [
            {"key": "decisions_tracked", "label": "Tracked decisions", "target": "all high-impact decisions"},
            {"key": "risk_register", "label": "Risks with owners", "target": ">= 5 risks or explicit none"},
            {"key": "weekly_cadence", "label": "Weekly cadence", "target": "defined with agenda and outputs"},
            {"key": "memory_coverage", "label": "Brain source coverage", "target": "Drive/Notion/Obsidian or waiver"},
        ],
        "quality_gates": [
            "Every priority must have an owner and next review date.",
            "Investor communications require approval.",
            "Risks must include severity and mitigation.",
            "Company Brain records must mark canonical operating docs.",
        ],
    },
    "support": {
        "north_star": "Support requests are triaged consistently, answered with approved macros, escalated correctly, and fed back into product.",
        "milestones": [
            {"day": 0, "title": "Issue taxonomy", "evidence": "Support issue map and severity categories complete."},
            {"day": 2, "title": "Triage and SLA workflow", "evidence": "Routing, SLA, escalation, and owner rules complete."},
            {"day": 4, "title": "Knowledge and macro package", "evidence": "Macros, help center plan, and customer tone rules complete."},
            {"day": 7, "title": "Feedback loop", "evidence": "Product feedback reporting and repeated-issue loop complete."},
        ],
        "kpis": [
            {"key": "issue_categories", "label": "Support categories", "target": ">= 6 categories or explicit fewer"},
            {"key": "macro_coverage", "label": "Macro coverage", "target": "top recurring issues"},
            {"key": "escalation_rules", "label": "Escalation rules", "target": "severity + owner + SLA"},
            {"key": "feedback_loop", "label": "Product feedback loop", "target": "ready"},
        ],
        "quality_gates": [
            "Automated customer messages require approval.",
            "Escalation must identify human owner for sensitive cases.",
            "Macros must include tone and exception handling.",
            "Feedback loop must identify product destination and cadence.",
        ],
    },
    "product": {
        "north_star": "A product team can move from ambiguity to validated scope, specs, architecture, roadmap, and release handoff.",
        "milestones": [
            {"day": 0, "title": "User/problem truth", "evidence": "Research brief and success metrics complete."},
            {"day": 3, "title": "Experience shape", "evidence": "UX flow, screen map, and usability risks complete."},
            {"day": 5, "title": "Technical plan", "evidence": "Architecture, API/data model, implementation sequence complete."},
            {"day": 7, "title": "Release plan", "evidence": "Roadmap, sprint plan, release checklist, and decisions complete."},
        ],
        "kpis": [
            {"key": "success_metrics", "label": "Success metrics", "target": "activation + retention/usage"},
            {"key": "spec_readiness", "label": "Spec readiness", "target": "engineering-ready"},
            {"key": "scope_approval", "label": "Release scope approval", "target": "approved or queued"},
            {"key": "delivery_risk", "label": "Delivery risks", "target": "identified with mitigations"},
        ],
        "quality_gates": [
            "Requirements must separate MVP from later scope.",
            "Every major feature must map to a user problem and success metric.",
            "Technical plan must include data model, API, and deployment risk.",
            "Release scope requires explicit approval before implementation handoff.",
        ],
    },
}


def build_stack_execution_contract(stack: AgentStackTemplate) -> dict[str, Any]:
    """Return the production operating contract for a stack."""
    specific = _STACK_CONTRACTS.get(stack.stack_id, {})
    cadence = {
        "standup": "Daily: agents publish blockers, outputs, and next action owner.",
        "review": "Weekly: founder reviews outcomes, approvals, and canonical Company Brain updates.",
        "handoff": "Every completed lane publishes artifacts, dependencies, and unresolved decisions.",
        "memory": "Canonical outputs are saved to Company Brain with version and visibility metadata.",
    }
    return {
        "stack_id": stack.stack_id,
        "stack_name": stack.name,
        "north_star": specific.get("north_star", stack.primary_outcome),
        "milestones": specific.get("milestones", []),
        "kpis": specific.get("kpis", []),
        "quality_gates": specific.get("quality_gates", []),
        "cadence": cadence,
        "handoff_rules": [
            "Each lane declares what it consumed, what it produced, and who should act next.",
            "Blocked outputs must state the missing connector, decision, or external dependency.",
            "Approval-gated actions are represented as durable approval workflow requests.",
            "Final handoff includes open risks, recommended next stack, and canonical memory updates.",
        ],
        "lane_contracts": [_lane_contract(stack, task) for task in stack.tasks],
    }


def task_execution_guidance(stack: AgentStackTemplate, task: StackTaskTemplate) -> str:
    """Compact guidance injected into agent prompts for one lane."""
    contract = build_stack_execution_contract(stack)
    lane = next((item for item in contract["lane_contracts"] if item["task_id"] == task.id), {})
    kpis = "; ".join(f"{item['label']} -> {item['target']}" for item in contract["kpis"][:4])
    gates = "; ".join(contract["quality_gates"][:4])
    return (
        "Production execution contract:\n"
        f"- Stack north star: {contract['north_star']}\n"
        f"- Lane proof: {lane.get('completion_evidence', 'Produce usable, specific artifacts and handoff notes.')}\n"
        f"- KPIs: {kpis or 'Produce measurable outputs tied to the outcome.'}\n"
        f"- Quality gates: {gates or 'Specific, approval-safe, and handoff-ready.'}\n"
        "- Handoff must include consumed context, produced artifacts, blockers, and next actor."
    )


def _lane_contract(stack: AgentStackTemplate, task: StackTaskTemplate) -> dict[str, Any]:
    artifact_titles = [
        artifact.title
        for artifact in stack.artifacts
        if artifact.key in set(task.artifacts)
    ]
    return {
        "task_id": task.id,
        "agent": task.agent,
        "title": task.title,
        "owns": artifact_titles,
        "depends_on": list(task.depends_on),
        "completion_evidence": (
            f"{task.title} is complete when {', '.join(artifact_titles) or 'lane output'} "
            "is specific to the goal, usable by dependent lanes, and saved to the session artifact ledger."
        ),
        "handoff_to": [
            downstream.id
            for downstream in stack.tasks
            if task.id in downstream.depends_on
        ],
    }
