"""Production bootstrap diagnostics for the final Astra launch proof."""

from __future__ import annotations

import argparse
import json
from typing import Any


def build_production_bootstrap(
    *,
    founder_id: str,
    stack_id: str = "idea_to_revenue",
    base_url: str = "",
    expected_backend_ip: str = "",
) -> dict[str, Any]:
    """Return exact setup steps needed before the final production proof can pass."""
    from backend.config import settings
    from backend.connector_setup import seed_stack_connector_credentials_from_env
    from backend.production_requirements import build_production_requirements

    requirements = build_production_requirements(founder_id=founder_id, stack_id=stack_id, base_url=base_url)
    seed_preview = seed_stack_connector_credentials_from_env(founder_id, stack_id, overwrite=False, dry_run=True)
    env_items = requirements.get("environment", [])
    missing_env = [item for item in env_items if item.get("required") and not item.get("configured")]
    required_connector_keys = {
        item.get("key")
        for item in requirements.get("connectors", [])
        if item.get("required")
    }
    seeded_connector_keys = {item.get("key") for item in seed_preview.get("seeded", [])}
    already_configured_keys = {
        item.get("key")
        for item in seed_preview.get("skipped", [])
        if item.get("reason") == "already_configured"
    }
    required_connector_seed_missing = sorted(required_connector_keys - seeded_connector_keys - already_configured_keys)
    commands = _commands(
        founder_id,
        requirements.get("stack_id") or stack_id,
        requirements.get("base_url") or base_url or settings.backend_url,
        expected_backend_ip=expected_backend_ip,
    )
    return {
        "ok": not missing_env and not required_connector_seed_missing,
        "founder_id": founder_id,
        "stack_id": requirements.get("stack_id") or stack_id,
        "base_url": requirements.get("base_url") or base_url,
        "expected_backend_ip": expected_backend_ip,
        "missing_env": [
            {
                "key": item.get("key"),
                "description": item.get("description"),
                "required": item.get("required"),
            }
            for item in missing_env
        ],
        "missing_env_count": len(missing_env),
        "connector_seed_preview": seed_preview,
        "required_connector_keys": sorted(required_connector_keys),
        "required_connector_seed_ready": not required_connector_seed_missing,
        "required_connector_seed_missing": required_connector_seed_missing,
        "final_proof_command": commands["final_proof"],
        "preflight_command": commands["preflight"],
        "readiness_command": commands["readiness"],
        "admin_final_proof_endpoint": requirements.get("final_gate", {}).get("admin_endpoint"),
        "admin_aggregate_manifest_verify_endpoint": requirements.get("final_gate", {}).get("aggregate_manifest_verify_endpoint"),
        "operator_steps": _operator_steps(missing_env, seed_preview, commands, required_connector_seed_missing),
        "summary": (
            "Production bootstrap prerequisites are present; run the final proof command."
            if not missing_env and not required_connector_seed_missing
            else f"Production bootstrap missing {len(missing_env)} env/config item(s) and {len(required_connector_seed_missing)} required connector seed(s) before final proof."
        ),
    }


def _commands(founder_id: str, stack_id: str, base_url: str, *, expected_backend_ip: str = "") -> dict[str, str]:
    founder = founder_id or "<prod_founder>"
    url = base_url or "$BACKEND_URL"
    expected_ip_arg = f" --expected-backend-ip {expected_backend_ip}" if expected_backend_ip else ""
    return {
        "preflight": f"python -m backend.production_preflight --base-url {url}{expected_ip_arg}",
        "readiness": f"python -m backend.launch_readiness --founder-id {founder} --stack-id {stack_id} --base-url {url} --report-id latest",
        "final_proof": f"python -m backend.production_launch --founder-id {founder} --stack-id {stack_id} --base-url {url} --live-connectors --seed-env-connectors",
    }


def _operator_steps(
    missing_env: list[dict[str, Any]],
    seed_preview: dict[str, Any],
    commands: dict[str, str],
    required_connector_seed_missing: list[str],
) -> list[str]:
    steps = []
    if missing_env:
        keys = ", ".join(str(item.get("key")) for item in missing_env)
        steps.append(f"Set required production env/config: {keys}.")
    if seed_preview.get("skipped_count"):
        skipped = [
            f"{item.get('key')} ({', '.join(item.get('missing_fields') or []) or item.get('reason')})"
            for item in seed_preview.get("skipped", [])
            if item.get("reason") == "missing_env"
        ]
        if skipped:
            steps.append(f"Optional connector env still missing: {', '.join(skipped)}.")
    if required_connector_seed_missing:
        steps.append(f"Set env or saved credentials for required connectors: {', '.join(required_connector_seed_missing)}.")
    steps.append("Restart backend/frontend so the production env is loaded.")
    steps.append(f"Run network preflight: {commands['preflight']}")
    steps.append(f"Run readiness check: {commands['readiness']}")
    steps.append(f"Run final proof: {commands['final_proof']}")
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(description="Show exact production bootstrap requirements for Astra final proof.")
    parser.add_argument("--founder-id", required=True)
    parser.add_argument("--stack-id", default="idea_to_revenue")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--expected-backend-ip", default="")
    args = parser.parse_args()
    result = build_production_bootstrap(
        founder_id=args.founder_id,
        stack_id=args.stack_id,
        base_url=args.base_url,
        expected_backend_ip=args.expected_backend_ip,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
