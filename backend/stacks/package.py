"""Goal-to-stack execution package builder.

This is the inspectable product primitive for Astra's core promise:
describe an outcome, receive the deployable AI department contract around it.
"""

from __future__ import annotations

from typing import Any

from backend.stacks.approvals import build_approval_queue
from backend.stacks.compiler import recommend_stack
from backend.stacks.manifest import build_stack_manifest
from backend.stacks.readiness import stack_readiness


def build_goal_stack_package(
    *,
    instruction: str,
    founder_id: str = "",
    company_stage: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    """Compile a business outcome into a deployable stack package."""
    recommendation = recommend_stack(instruction, company_stage)
    stack = recommendation.stack
    manifest = build_stack_manifest(stack, instruction, company_name)
    readiness = stack_readiness(founder_id, stack.stack_id) if founder_id else None
    approval_queue = build_approval_queue(stack)
    required_connectors = manifest.get("connectors", {}).get("required", [])
    optional_connectors = manifest.get("connectors", {}).get("optional", [])
    missing_required = [
        item.get("key")
        for item in (readiness or {}).get("connectors", [])
        if item.get("required") and not item.get("connected")
    ]

    return {
        "ok": True,
        "instruction": instruction,
        "founder_id": founder_id,
        "company_stage": company_stage or "",
        "company_name": company_name or "",
        "recommendation": recommendation.to_public_dict(),
        "stack_id": stack.stack_id,
        "stack_name": stack.name,
        "confidence": recommendation.confidence,
        "matched_signals": recommendation.matched_signals,
        "deployable": not missing_required if readiness else True,
        "blocked_by": missing_required,
        "manifest": manifest,
        "execution_blueprint": manifest["operating_plan"]["execution_blueprint"],
        "operating_plan": manifest["operating_plan"],
        "approval_queue": approval_queue,
        "connector_setup": {
            "required": required_connectors,
            "optional": optional_connectors,
            "missing_required": missing_required,
            "rule": manifest.get("connectors", {}).get("rule"),
        },
        "readiness": readiness,
        "start_payload": {
            "founder_id": founder_id or "<founder_id>",
            "instruction": instruction,
            "stack_id": stack.stack_id,
            "constraints": {
                "stack_id": stack.stack_id,
                "company_stage": company_stage or "",
                "company_name": company_name or "",
            },
        },
        "proof": {
            "contract": "business_outcome_to_deployable_ai_department",
            "has_manifest": bool(manifest),
            "has_execution_blueprint": bool(manifest["operating_plan"].get("execution_blueprint")),
            "has_connector_plan": bool(required_connectors or optional_connectors),
            "has_approval_policy": bool(manifest.get("approvals")),
            "has_artifact_contract": bool(manifest.get("outputs")),
            "has_memory_policy": bool(manifest.get("memory_policy")),
            "has_human_collaboration_model": bool(manifest.get("human_collaboration")),
        },
        "summary": (
            f"Astra selected {stack.name} with {recommendation.confidence:.0%} confidence "
            f"and compiled {len(manifest['workflow']['nodes'])} lanes, "
            f"{len(manifest['outputs'])} outputs, {len(required_connectors)} required connectors, "
            f"and {len(manifest['approvals'])} approval gates."
        ),
    }
