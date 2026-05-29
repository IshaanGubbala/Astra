from backend.config import settings
from backend.production_requirements import build_production_requirements
import pytest


def test_production_requirements_names_env_and_required_connectors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "backend_url", "http://localhost:8000")
    monkeypatch.setattr(settings, "frontend_url", "http://localhost:3003")
    monkeypatch.setattr(settings, "astra_require_auth", False)
    monkeypatch.setattr(settings, "astra_platform_admins", "")
    monkeypatch.setattr(settings, "astra_jwt_secret", "")
    monkeypatch.setattr(settings, "astra_jwt_jwks_url", "")
    monkeypatch.setattr(settings, "astra_trust_auth_headers", False)
    monkeypatch.setattr(settings, "astra_creds_key", "")
    monkeypatch.setattr(settings, "astra_alert_webhook_url", "")
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "")
    monkeypatch.setattr(settings, "stripe_price_starter", "")
    monkeypatch.setattr(settings, "stripe_price_team", "")
    monkeypatch.setattr(settings, "stripe_price_scale", "")

    report = build_production_requirements(founder_id="founder_prod", stack_id="idea_to_revenue")

    assert report["ok"] is False
    assert "ASTRA_CREDS_KEY" in report["missing"]
    assert "github" in report["required_connector_keys"]
    assert "vercel" in report["required_connector_keys"]
    assert report["objective_evidence"]["code_contract_ready"] is True
    assert report["objective_evidence"]["production_proven"] is False
    assert report["final_gate"]["requires_live_connectors"] is True
    assert "--live-connectors" in report["final_gate"]["command"]
    assert "--seed-env-connectors" in report["final_gate"]["command"]
    assert "backend.production_launch" in report["final_gate"]["command"]
    assert report["final_gate"]["seed_env_connectors_flag"] == "--seed-env-connectors"
    assert ".astra/production_verification/latest.sha256.json" in report["final_gate"]["writes"]
    assert ".astra/production_launch/latest.sha256.json" in report["final_gate"]["writes"]
    assert report["final_gate"]["verify_manifest_endpoint"].endswith("/manifest/verify")
    assert report["final_gate"]["bundle_endpoint"].endswith("/bundle")
    assert report["final_gate"]["aggregate_proof_endpoint"].endswith("/production-launch/reports/latest")
    assert report["final_gate"]["aggregate_manifest_verify_endpoint"].endswith("/production-launch/reports/latest/manifest/verify")


def test_production_requirements_pass_configured_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "backend_url", "https://api.astracreates.com")
    monkeypatch.setattr(settings, "frontend_url", "https://app.astracreates.com")
    monkeypatch.setattr(settings, "astra_require_auth", True)
    monkeypatch.setattr(settings, "astra_platform_admins", "admin_1")
    monkeypatch.setattr(settings, "astra_jwt_secret", "secret")
    monkeypatch.setattr(settings, "astra_creds_key", "creds")
    monkeypatch.setattr(settings, "astra_alert_webhook_url", "https://hooks.example/astra")
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_live")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_live")
    monkeypatch.setattr(settings, "stripe_price_starter", "price_starter")
    monkeypatch.setattr(settings, "stripe_price_team", "price_team")
    monkeypatch.setattr(settings, "stripe_price_scale", "price_scale")

    report = build_production_requirements(founder_id="founder_prod", stack_id="sales")

    assert report["ok"] is True
    assert report["missing"] == []
    assert report["stack_id"] == "sales"


@pytest.mark.asyncio
async def test_admin_production_requirements_endpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from backend.api.admin import production_requirements

    report = await production_requirements(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
    )

    assert report["founder_id"] == "founder_prod"
    assert report["stack_id"] == "idea_to_revenue"
    assert report["final_gate"]["admin_endpoint"] == "/admin/production-launch"
    assert report["objective_evidence"]["stack_id"] == "idea_to_revenue"
