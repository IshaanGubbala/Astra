"""Production setup requirements for Astra operator launch prep."""

from __future__ import annotations

from typing import Any


def build_production_requirements(
    *,
    founder_id: str = "",
    stack_id: str = "idea_to_revenue",
    base_url: str = "",
    require_final_launch_proof: bool = True,
) -> dict[str, Any]:
    """Return the exact production requirements before final verification."""
    from backend.billing import billing_config_status
    from backend.config import settings
    from backend.connector_validation import _FIELD_SPECS
    from backend.objective_readiness import build_objective_evidence_matrix
    from backend.stacks.templates import get_stack_template

    stack = get_stack_template(stack_id)
    billing = billing_config_status()
    backend_url = base_url or settings.backend_url
    objective_evidence = build_objective_evidence_matrix(
        founder_id=founder_id,
        stack_id=stack.stack_id,
        base_url=backend_url,
        require_final_launch_proof=require_final_launch_proof,
    )

    env = [
        _env("BACKEND_URL", "Public backend API URL used by callbacks and smoke checks.", bool(backend_url and backend_url.startswith("https://")), backend_url),
        _env("FRONTEND_URL", "Public app URL used by billing/auth redirects.", bool(settings.frontend_url and settings.frontend_url.startswith("https://")), settings.frontend_url),
        _env("ASTRA_REQUIRE_AUTH", "Enable production auth enforcement.", bool(settings.astra_require_auth), str(settings.astra_require_auth)),
        _env("ASTRA_PLATFORM_ADMINS", "Comma-separated platform admin user IDs.", bool(settings.astra_platform_admins), _redact(settings.astra_platform_admins)),
        _env("ASTRA_JWT_JWKS_URL or ASTRA_JWT_SECRET", "JWT verification source for API/admin auth.", bool(settings.astra_jwt_jwks_url or settings.astra_jwt_secret or settings.astra_trust_auth_headers), "configured" if settings.astra_jwt_jwks_url or settings.astra_jwt_secret or settings.astra_trust_auth_headers else ""),
        _env("ASTRA_CREDS_KEY", "Stable encryption key for saved connector credentials.", bool(settings.astra_creds_key), _redact(settings.astra_creds_key)),
        _env("ASTRA_ALERT_WEBHOOK_URL", "Operations alert delivery webhook.", bool(settings.astra_alert_webhook_url), _redact(settings.astra_alert_webhook_url)),
        _env("STRIPE_SECRET_KEY", "Stripe API key for self-serve billing.", bool(settings.stripe_secret_key), _redact(settings.stripe_secret_key)),
        _env("STRIPE_WEBHOOK_SECRET", "Stripe webhook signature secret.", bool(settings.stripe_webhook_secret), _redact(settings.stripe_webhook_secret)),
        _env("STRIPE_PRICE_STARTER", "Stripe price id for Starter plan.", "starter" not in billing.get("missing_price_ids", []), _redact(settings.stripe_price_starter)),
        _env("STRIPE_PRICE_TEAM", "Stripe price id for Team plan.", "team" not in billing.get("missing_price_ids", []), _redact(settings.stripe_price_team)),
        _env("STRIPE_PRICE_SCALE", "Stripe price id for Scale plan.", "scale" not in billing.get("missing_price_ids", []), _redact(settings.stripe_price_scale)),
    ]

    connectors = []
    for connector in stack.connector_requirements:
        field_specs = _FIELD_SPECS.get(connector.key, [{"key": "token", "required": True}])
        connectors.append({
            "key": connector.key,
            "label": connector.label,
            "category": connector.category,
            "purpose": connector.purpose,
            "required": connector.required,
            "credential_fields": [
                {"key": field["key"], "required": bool(field.get("required", False))}
                for field in field_specs
            ],
            "live_validation_required": bool(connector.required),
        })

    hard_missing = [item["key"] for item in env if item["required"] and not item["configured"]]
    required_connectors = [item["key"] for item in connectors if item["required"]]
    return {
        "ok": not hard_missing,
        "founder_id": founder_id,
        "stack_id": stack.stack_id,
        "stack_name": stack.name,
        "base_url": backend_url,
        "environment": env,
        "billing": billing,
        "objective_evidence": objective_evidence,
        "require_final_launch_proof": require_final_launch_proof,
        "connectors": connectors,
        "required_connector_keys": required_connectors,
        "final_gate": {
            "command": _verification_command(founder_id, stack.stack_id, backend_url),
            "admin_endpoint": "/admin/production-launch",
            "seed_env_connectors_flag": "--seed-env-connectors",
            "requires_live_connectors": True,
            "writes": [
                ".astra/production_smoke/latest.json",
                ".astra/production_verification/latest.json",
                ".astra/production_verification/latest.md",
                ".astra/production_verification/latest.sha256.json",
                ".astra/production_launch/latest.json",
                ".astra/production_launch/latest.sha256.json",
            ],
            "verify_manifest_endpoint": "/admin/production-verification/reports/latest/manifest/verify",
            "bundle_endpoint": "/admin/production-verification/reports/latest/bundle",
            "aggregate_proof_endpoint": "/admin/production-launch/reports/latest",
            "aggregate_manifest_verify_endpoint": "/admin/production-launch/reports/latest/manifest/verify",
        },
        "missing": hard_missing,
        "summary": (
            f"{stack.name} production requirements are configured."
            if not hard_missing
            else f"{stack.name} production setup missing {len(hard_missing)} env/config item(s)."
        ),
    }


def _env(key: str, description: str, configured: bool, current: str = "", required: bool = True) -> dict[str, Any]:
    return {
        "key": key,
        "description": description,
        "required": required,
        "configured": bool(configured),
        "current": current,
    }


def _redact(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return f"{value[:3]}...{value[-3:]}"


def _verification_command(founder_id: str, stack_id: str, base_url: str) -> str:
    founder = founder_id or "<prod_founder>"
    url = base_url or "https://api.astracreates.com"
    return f"python -m backend.production_launch --founder-id {founder} --stack-id {stack_id} --base-url {url} --live-connectors --seed-env-connectors"
