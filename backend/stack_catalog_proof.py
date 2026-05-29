"""Catalog-level proof that every promised Agent Stack compiles for execution."""

from __future__ import annotations

from typing import Any


def build_stack_catalog_proof(*, sample_goal: str = "Build the next operating system for this business.") -> dict[str, Any]:
    """Verify every promised template can become a deployable AI department package."""
    from backend.stacks.execution_blueprint import build_stack_execution_blueprint
    from backend.stacks.execution_contracts import build_stack_execution_contract
    from backend.stacks.template_quality import audit_stack_template
    from backend.stacks.templates import PROMISED_AGENT_STACK_IDS, STACK_TEMPLATES

    stack_reports = []
    for stack_id in PROMISED_AGENT_STACK_IDS:
        stack = STACK_TEMPLATES.get(stack_id)
        if not stack:
            stack_reports.append({
                "stack_id": stack_id,
                "ok": False,
                "missing_template": True,
                "gaps": ["Template is missing from STACK_TEMPLATES."],
            })
            continue
        quality = audit_stack_template(stack)
        contract = build_stack_execution_contract(stack)
        blueprint = build_stack_execution_blueprint(stack, sample_goal, company_name="Astra Proof")
        stack_reports.append(_stack_report(stack_id, stack, quality, contract, blueprint))

    failed = [item for item in stack_reports if not item.get("ok")]
    return {
        "ok": not failed and bool(stack_reports),
        "stack_count": len(stack_reports),
        "ready_count": len(stack_reports) - len(failed),
        "failed_count": len(failed),
        "stacks": stack_reports,
        "failed": failed,
        "summary": (
            f"All {len(stack_reports)} promised Agent Stacks compile into deployable execution packages."
            if not failed and stack_reports
            else f"{len(failed)} promised Agent Stack package(s) failed catalog proof."
        ),
    }


def _stack_report(stack_id: str, stack: Any, quality: dict[str, Any], contract: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, Any]:
    tasks = list(getattr(stack, "tasks", []) or [])
    artifacts = list(getattr(stack, "artifacts", []) or [])
    connectors = list(getattr(stack, "connector_requirements", []) or [])
    approvals = list(getattr(stack, "approval_gates", []) or [])
    lanes = blueprint.get("lanes") or []
    lane_ids = {lane.get("id") for lane in lanes}
    artifact_matrix = blueprint.get("artifact_acceptance_matrix") or []
    artifact_owners = {item.get("artifact_key"): item.get("owner_lane") for item in artifact_matrix}
    connector_dependencies = blueprint.get("connector_dependencies") or []
    gaps: list[str] = []

    if not quality.get("ready"):
        gaps.extend(str(gap) for gap in quality.get("gaps", []))
    if len(lanes) != len(tasks):
        gaps.append("Blueprint lane count does not match template task count.")
    if {task.id for task in tasks} - lane_ids:
        gaps.append("Blueprint is missing one or more task lanes.")
    if not contract.get("north_star"):
        gaps.append("Execution contract is missing a north star.")
    if len(contract.get("milestones") or []) < 3:
        gaps.append("Execution contract needs at least three milestones.")
    if len(contract.get("kpis") or []) < 3:
        gaps.append("Execution contract needs at least three KPIs.")
    if len(contract.get("quality_gates") or []) < 3:
        gaps.append("Execution contract needs at least three quality gates.")
    if len(artifact_matrix) != len(artifacts):
        gaps.append("Artifact acceptance matrix does not cover every template artifact.")
    missing_artifact_owners = [artifact.key for artifact in artifacts if not artifact_owners.get(artifact.key)]
    if missing_artifact_owners:
        gaps.append("Artifacts missing owner lanes: " + ", ".join(missing_artifact_owners))
    lanes_without_deliverables = [lane.get("id") for lane in lanes if not lane.get("deliverables")]
    if lanes_without_deliverables:
        gaps.append("Lanes missing deliverables: " + ", ".join(str(item) for item in lanes_without_deliverables))
    if connectors and not connector_dependencies:
        gaps.append("Connector dependencies are not represented in blueprint.")
    if approvals and not blueprint.get("approvals"):
        gaps.append("Approval gates are not represented in blueprint.")
    if not blueprint.get("completion_audit"):
        gaps.append("Blueprint is missing completion audit criteria.")

    return {
        "stack_id": stack_id,
        "stack_name": getattr(stack, "name", stack_id),
        "ok": not gaps,
        "quality_score": quality.get("score"),
        "task_count": len(tasks),
        "lane_count": len(lanes),
        "artifact_count": len(artifacts),
        "artifact_acceptance_count": len(artifact_matrix),
        "connector_count": len(connectors),
        "approval_count": len(approvals),
        "milestone_count": len(contract.get("milestones") or []),
        "kpi_count": len(contract.get("kpis") or []),
        "quality_gate_count": len(contract.get("quality_gates") or []),
        "gaps": gaps,
    }
