"""Quality audit for deployable Agent Stack templates.

This prevents Astra's product contract from regressing into shallow "agent
lists". A stack is production-shaped only when it has enough lanes, artifacts,
approval policy, connector requirements, dashboards, milestones, KPIs, and
handoff structure to behave like an AI department.
"""

from __future__ import annotations

from typing import Any

from backend.stacks.execution_contracts import build_stack_execution_contract
from backend.stacks.templates import AgentStackTemplate


MIN_TASKS = 4
MIN_ARTIFACTS = 8
MIN_CONNECTORS = 4
MIN_DASHBOARDS = 5
MIN_MILESTONES = 4
MIN_KPIS = 4
MIN_QUALITY_GATES = 4


def audit_stack_template(stack: AgentStackTemplate) -> dict[str, Any]:
    """Return a structured production-depth audit for one stack."""
    contract = build_stack_execution_contract(stack)
    artifact_keys = {artifact.key for artifact in stack.artifacts}
    task_ids = {task.id for task in stack.tasks}
    required_connectors = [connector for connector in stack.connector_requirements if connector.required]
    referenced_artifacts = {artifact for task in stack.tasks for artifact in task.artifacts}
    missing_artifact_refs = sorted(referenced_artifacts - artifact_keys)
    orphan_artifacts = sorted(artifact_keys - referenced_artifacts)
    invalid_dependencies = sorted({
        dependency
        for task in stack.tasks
        for dependency in task.depends_on
        if dependency not in task_ids
    })
    downstream_count = {
        task.id: sum(1 for downstream in stack.tasks if task.id in downstream.depends_on)
        for task in stack.tasks
    }
    terminal_tasks = [task for task in stack.tasks if downstream_count.get(task.id, 0) == 0]
    lane_contracts = contract.get("lane_contracts") or []

    checks = [
        _check("minimum_lanes", len(stack.tasks) >= MIN_TASKS, f"{len(stack.tasks)}/{MIN_TASKS} lanes"),
        _check("minimum_artifacts", len(stack.artifacts) >= MIN_ARTIFACTS, f"{len(stack.artifacts)}/{MIN_ARTIFACTS} artifacts"),
        _check("minimum_connectors", len(stack.connector_requirements) >= MIN_CONNECTORS, f"{len(stack.connector_requirements)}/{MIN_CONNECTORS} connectors"),
        _check("required_connector", bool(required_connectors), f"{len(required_connectors)} required connectors"),
        _check("approval_policy", bool(stack.approval_gates), f"{len(stack.approval_gates)} approval gates"),
        _check("dashboard_surface", len(stack.dashboard_sections) >= MIN_DASHBOARDS, f"{len(stack.dashboard_sections)}/{MIN_DASHBOARDS} dashboards"),
        _check("milestones", len(contract.get("milestones") or []) >= MIN_MILESTONES, f"{len(contract.get('milestones') or [])}/{MIN_MILESTONES} milestones"),
        _check("kpis", len(contract.get("kpis") or []) >= MIN_KPIS, f"{len(contract.get('kpis') or [])}/{MIN_KPIS} KPIs"),
        _check("quality_gates", len(contract.get("quality_gates") or []) >= MIN_QUALITY_GATES, f"{len(contract.get('quality_gates') or [])}/{MIN_QUALITY_GATES} quality gates"),
        _check("artifact_refs_valid", not missing_artifact_refs, ", ".join(missing_artifact_refs) or "all task artifacts exist"),
        _check("no_orphan_artifacts", not orphan_artifacts, ", ".join(orphan_artifacts) or "all artifacts owned by lanes"),
        _check("dependencies_valid", not invalid_dependencies, ", ".join(invalid_dependencies) or "all dependencies point to lanes"),
        _check("handoff_terminal_lane", any(task.agent == "ops" for task in terminal_tasks), "terminal lane should include ops synthesis"),
        _check("lane_contracts", len(lane_contracts) == len(stack.tasks), f"{len(lane_contracts)}/{len(stack.tasks)} lane contracts"),
    ]
    score = round(sum(1 for check in checks if check["ok"]) / len(checks) * 100)
    gaps = [check for check in checks if not check["ok"]]
    return {
        "stack_id": stack.stack_id,
        "stack_name": stack.name,
        "score": score,
        "ready": not gaps,
        "checks": checks,
        "gaps": gaps,
        "summary": "Production-depth stack template is ready." if not gaps else f"{len(gaps)} template depth gaps remain.",
    }


def _check(key: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"key": key, "ok": bool(ok), "detail": detail}
