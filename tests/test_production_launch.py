import pytest

from backend.config import settings
from pathlib import Path

from backend.production_launch import (
    get_final_launch_proof,
    get_final_launch_proof_manifest,
    run_final_launch_proof,
    verify_final_launch_proof_manifest,
)


def _configure_prod_env(monkeypatch):
    monkeypatch.setattr(settings, "backend_url", "https://api.astracreates.com")
    monkeypatch.setattr(settings, "frontend_url", "https://app.astracreates.com")
    monkeypatch.setattr(settings, "astra_require_auth", True)
    monkeypatch.setattr(settings, "astra_platform_admins", "admin_1")
    monkeypatch.setattr(settings, "astra_jwt_secret", "secret")
    monkeypatch.setattr(settings, "astra_jwt_jwks_url", "")
    monkeypatch.setattr(settings, "astra_trust_auth_headers", False)
    monkeypatch.setattr(settings, "astra_creds_key", "creds")
    monkeypatch.setattr(settings, "astra_alert_webhook_url", "https://hooks.example/astra")
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_live")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_live")
    monkeypatch.setattr(settings, "stripe_price_starter", "price_starter")
    monkeypatch.setattr(settings, "stripe_price_team", "price_team")
    monkeypatch.setattr(settings, "stripe_price_scale", "price_scale")


def test_final_launch_proof_runs_full_success_sequence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _configure_prod_env(monkeypatch)
    monkeypatch.setattr("backend.production_smoke.run_production_smoke", lambda **kwargs: {
        "ok": True,
        "created_at": "2026-05-29T00:00:00Z",
        "stack_id": kwargs["stack_id"],
        "failed_count": 0,
        "summary": "production smoke passed",
        "checks": [],
        "deploy_evidence": {"ok": True, "summary": "complete", "missing": [], "checks": []},
    })

    result = run_final_launch_proof(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
        live_connectors=True,
    )

    assert result["ok"] is True
    assert result["stack_catalog_proof"]["ok"] is True
    assert result["stack_catalog_proof"]["ready_count"] == 6
    assert result["verification"]["ok"] is True
    assert result["manifest"]["verified"] is True
    assert result["bundle"]["ok"] is True
    assert result["launch_readiness"]["ok"] is True
    assert result["paths"]["latest_json"].endswith(".astra/production_launch/latest.json")
    assert result["paths"]["latest_manifest"].endswith(".astra/production_launch/latest.sha256.json")
    assert result["evidence_manifest"]["algorithm"] == "sha256"
    saved = get_final_launch_proof(result["id"])
    latest = get_final_launch_proof()
    manifest = get_final_launch_proof_manifest(result["id"])
    verification = verify_final_launch_proof_manifest(result["id"])
    assert saved["found"] is True
    assert latest["proof"]["id"] == result["id"]
    assert manifest["found"] is True
    assert verification["verified"] is True


def test_final_launch_proof_can_seed_env_connector_credentials(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")
    _configure_prod_env(monkeypatch)
    monkeypatch.setattr(settings, "github_token", "ghp_secret")
    monkeypatch.setattr(settings, "vercel_token", "vercel_secret")
    monkeypatch.setattr("backend.production_smoke.run_production_smoke", lambda **kwargs: {
        "ok": True,
        "created_at": "2026-05-29T00:00:00Z",
        "stack_id": kwargs["stack_id"],
        "failed_count": 0,
        "summary": "production smoke passed",
        "checks": [],
        "deploy_evidence": {"ok": True, "summary": "complete", "missing": [], "checks": []},
    })

    result = run_final_launch_proof(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
        live_connectors=True,
        seed_env_connectors=True,
    )

    assert result["ok"] is True
    seeded_keys = {item["key"] for item in result["connector_seed"]["seeded"]}
    assert result["connector_seed"]["seeded_count"] >= 2
    assert {"github", "vercel"}.issubset(seeded_keys)
    assert "ghp_secret" not in str(result["connector_seed"])
    assert "vercel_secret" not in str(result["connector_seed"])


def test_final_launch_proof_manifest_detects_tampering(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _configure_prod_env(monkeypatch)
    monkeypatch.setattr("backend.production_smoke.run_production_smoke", lambda **kwargs: {
        "ok": True,
        "created_at": "2026-05-29T00:00:00Z",
        "stack_id": kwargs["stack_id"],
        "failed_count": 0,
        "summary": "production smoke passed",
        "checks": [],
        "deploy_evidence": {"ok": True, "summary": "complete", "missing": [], "checks": []},
    })

    result = run_final_launch_proof(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
        live_connectors=True,
    )
    Path(result["paths"]["json"]).write_text('{"tampered": true}')

    verification = verify_final_launch_proof_manifest(result["id"])

    assert verification["verified"] is False
    assert any(check["key"] == "json" for check in verification["failed"])


def test_final_launch_proof_fails_when_live_connector_gate_not_requested(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _configure_prod_env(monkeypatch)
    monkeypatch.setattr("backend.production_smoke.run_production_smoke", lambda **kwargs: {
        "ok": False,
        "created_at": "2026-05-29T00:00:00Z",
        "stack_id": kwargs["stack_id"],
        "failed_count": 1,
        "summary": "production smoke failed: 1 check(s)",
        "checks": [{"key": "strict_live_connectors_requested", "ok": False}],
        "deploy_evidence": {"ok": False, "summary": "missing live connectors", "missing": ["--live-connectors"], "checks": []},
    })

    result = run_final_launch_proof(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
        live_connectors=False,
    )

    assert result["ok"] is False
    assert result["verification"]["ok"] is False
    assert result["launch_readiness"]["ok"] is False


@pytest.mark.asyncio
async def test_admin_production_launch_endpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _configure_prod_env(monkeypatch)
    monkeypatch.setattr("backend.production_smoke.run_production_smoke", lambda **kwargs: {
        "ok": True,
        "created_at": "2026-05-29T00:00:00Z",
        "stack_id": kwargs["stack_id"],
        "failed_count": 0,
        "summary": "production smoke passed",
        "checks": [],
        "deploy_evidence": {"ok": True, "summary": "complete", "missing": [], "checks": []},
    })
    from backend.api.admin import (
        production_launch,
        production_launch_report,
        production_launch_report_manifest,
        production_launch_report_manifest_verify,
    )

    result = await production_launch(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
        live_connectors=True,
        seed_env_connectors=False,
    )

    assert result["ok"] is True
    assert result["launch_readiness"]["ok"] is True
    fetched = await production_launch_report(result["id"])
    latest = await production_launch_report("latest")
    manifest = await production_launch_report_manifest(result["id"])
    manifest_verification = await production_launch_report_manifest_verify(result["id"])
    assert fetched["proof"]["id"] == result["id"]
    assert latest["proof"]["id"] == result["id"]
    assert manifest["manifest"]["proof_id"] == result["id"]
    assert manifest_verification["verified"] is True
