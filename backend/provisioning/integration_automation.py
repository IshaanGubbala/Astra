"""Deterministic integration auto-connect orchestration.

This module separates integrations into:
- platform-managed: can be auto-connected with server-side credentials.
- oauth-required: requires end-user OAuth consent and cannot be zero-touch.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.config import settings
from backend.provisioning.credentials_store import store_credentials


@dataclass(frozen=True)
class ServiceSpec:
    service: str
    label: str
    mode: str  # "platform_managed" | "oauth_required"
    setting_key: str | None = None
    credential_field: str | None = None
    reason: str = ""


SERVICE_SPECS: list[ServiceSpec] = [
    ServiceSpec("github", "GitHub", "platform_managed", "github_token", "token"),
    ServiceSpec("vercel", "Vercel", "platform_managed", "vercel_token", "token"),
    ServiceSpec("sendgrid", "SendGrid", "platform_managed", "sendgrid_api_key", "api_key"),
    ServiceSpec("resend", "Resend", "platform_managed", "resend_api_key", "api_key"),
    ServiceSpec("cloudflare", "Cloudflare", "platform_managed", "cloudflare_api_token", "api_token"),
    ServiceSpec("notion", "Notion", "platform_managed", "notion_token", "token"),
    ServiceSpec("posthog", "PostHog", "platform_managed", "posthog_api_key", "api_key"),
    ServiceSpec("clerk", "Clerk", "platform_managed", "clerk_secret_key", "secret_key"),
    ServiceSpec("meta_ads", "Meta Ads", "platform_managed", "meta_access_token", "access_token"),
    ServiceSpec("instagram", "Instagram", "platform_managed", "instagram_access_token", "access_token"),
    ServiceSpec("composio", "Composio Core", "platform_managed", "composio_api_key", "api_key"),
    ServiceSpec(
        "supabase_management",
        "Supabase Management",
        "platform_managed",
        "supabase_management_token",
        "management_token",
    ),
    ServiceSpec(
        "composio_gmail",
        "Composio Gmail",
        "oauth_required",
        reason="Google OAuth consent is required per end-user account.",
    ),
    ServiceSpec(
        "composio_linkedin",
        "Composio LinkedIn",
        "oauth_required",
        reason="LinkedIn OAuth consent is required per end-user account.",
    ),
    ServiceSpec(
        "composio_linear",
        "Composio Linear",
        "oauth_required",
        reason="Linear OAuth consent is required per end-user account.",
    ),
    ServiceSpec(
        "composio_notion",
        "Composio Notion",
        "oauth_required",
        reason="Notion OAuth consent is required per end-user account.",
    ),
    ServiceSpec(
        "composio_googlecalendar",
        "Composio Google Calendar",
        "oauth_required",
        reason="Google OAuth consent is required per end-user account.",
    ),
]


def _setting_value(setting_key: str | None) -> str:
    if not setting_key:
        return ""
    return (getattr(settings, setting_key, "") or "").strip()


def apply_platform_credentials(founder_id: str) -> dict[str, bool]:
    """Store all available platform-managed credentials for a founder."""
    mapped: dict[str, bool] = {}
    for spec in SERVICE_SPECS:
        if spec.mode != "platform_managed":
            continue
        raw = _setting_value(spec.setting_key)
        if not raw or not spec.credential_field:
            continue
        store_credentials(founder_id, spec.service, {spec.credential_field: raw})
        mapped[spec.service] = True
    return mapped


def auto_connect_status(founder_id: str, apply: bool = False) -> dict[str, Any]:
    """Return deterministic auto-connect status for every known integration."""
    if apply:
        apply_platform_credentials(founder_id)

    services: list[dict[str, Any]] = []
    for spec in SERVICE_SPECS:
        if spec.mode == "oauth_required":
            services.append(
                {
                    "service": spec.service,
                    "label": spec.label,
                    "mode": spec.mode,
                    "status": "user_oauth_required",
                    "reason": spec.reason,
                }
            )
            continue

        configured = bool(_setting_value(spec.setting_key))
        services.append(
            {
                "service": spec.service,
                "label": spec.label,
                "mode": spec.mode,
                "status": "auto_connected" if configured else "missing_platform_key",
                "reason": ""
                if configured
                else f"Missing platform credential: {spec.setting_key}",
            }
        )

    auto_connected = sum(1 for row in services if row["status"] == "auto_connected")
    oauth_required = sum(1 for row in services if row["status"] == "user_oauth_required")
    missing_platform = sum(1 for row in services if row["status"] == "missing_platform_key")

    return {
        "founder_id": founder_id,
        "summary": {
            "auto_connected": auto_connected,
            "oauth_required": oauth_required,
            "missing_platform": missing_platform,
            "zero_touch_possible": oauth_required == 0,
        },
        "services": services,
    }
