import pytest

from backend.config import settings
from backend.production_bootstrap import build_production_bootstrap
from backend.provisioning.credentials_store import load_all_credentials


def test_production_bootstrap_reports_missing_env_and_final_command(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")
    monkeypatch.setattr(settings, "backend_url", "http://localhost:8000")
    monkeypatch.setattr(settings, "frontend_url", "http://localhost:3003")
    monkeypatch.setattr(settings, "astra_require_auth", False)
    monkeypatch.setattr(settings, "astra_platform_admins", "")
    monkeypatch.setattr(settings, "astra_jwt_secret", "")
    monkeypatch.setattr(settings, "astra_jwt_jwks_url", "")
    monkeypatch.setattr(settings, "astra_creds_key", "")
    monkeypatch.setattr(settings, "astra_alert_webhook_url", "")
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "")
    monkeypatch.setattr(settings, "stripe_price_starter", "")
    monkeypatch.setattr(settings, "stripe_price_team", "")
    monkeypatch.setattr(settings, "stripe_price_scale", "")
    monkeypatch.setattr(settings, "github_token", "")
    monkeypatch.setattr(settings, "vercel_token", "")

    result = build_production_bootstrap(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
        expected_backend_ip="167.235.151.204",
    )

    missing_keys = {item["key"] for item in result["missing_env"]}
    assert result["ok"] is False
    assert "ASTRA_REQUIRE_AUTH" in missing_keys
    assert "STRIPE_SECRET_KEY" in missing_keys
    assert result["required_connector_keys"] == ["github", "vercel"]
    assert result["required_connector_seed_ready"] is False
    assert result["required_connector_seed_missing"] == ["github", "vercel"]
    assert "--expected-backend-ip 167.235.151.204" in result["preflight_command"]
    assert "--seed-env-connectors" in result["final_proof_command"]
    assert any("Run network preflight" in step for step in result["operator_steps"])
    assert any("Run final proof" in step for step in result["operator_steps"])


def test_production_bootstrap_does_not_return_seeded_secret_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")
    monkeypatch.setattr(settings, "backend_url", "https://api.astracreates.com")
    monkeypatch.setattr(settings, "frontend_url", "https://app.astracreates.com")
    monkeypatch.setattr(settings, "astra_require_auth", True)
    monkeypatch.setattr(settings, "astra_platform_admins", "admin_1")
    monkeypatch.setattr(settings, "astra_jwt_secret", "jwt_secret")
    monkeypatch.setattr(settings, "astra_jwt_jwks_url", "")
    monkeypatch.setattr(settings, "astra_creds_key", "creds_key")
    monkeypatch.setattr(settings, "astra_alert_webhook_url", "https://hooks.example/astra")
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_live_secret")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_secret")
    monkeypatch.setattr(settings, "stripe_price_starter", "price_starter")
    monkeypatch.setattr(settings, "stripe_price_team", "price_team")
    monkeypatch.setattr(settings, "stripe_price_scale", "price_scale")
    monkeypatch.setattr(settings, "github_token", "ghp_secret")
    monkeypatch.setattr(settings, "vercel_token", "vercel_secret")

    result = build_production_bootstrap(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
    )

    assert result["missing_env_count"] == 0
    assert result["connector_seed_preview"]["seeded_count"] >= 2
    assert result["required_connector_seed_ready"] is True
    assert result["required_connector_seed_missing"] == []
    assert result["connector_seed_preview"]["dry_run"] is True
    assert load_all_credentials("founder_prod") == {}
    assert "ghp_secret" not in str(result)
    assert "vercel_secret" not in str(result)


@pytest.mark.asyncio
async def test_admin_production_bootstrap_endpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from backend.api.admin import production_bootstrap

    result = await production_bootstrap(
        founder_id="founder_prod",
        stack_id="sales",
        base_url="https://api.astracreates.com",
        expected_backend_ip="167.235.151.204",
    )

    assert result["founder_id"] == "founder_prod"
    assert result["stack_id"] == "sales"
    assert result["expected_backend_ip"] == "167.235.151.204"
    assert "backend.production_launch" in result["final_proof_command"]
