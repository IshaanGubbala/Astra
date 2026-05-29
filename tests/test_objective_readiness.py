from backend.objective_readiness import build_objective_evidence_matrix, build_objective_readiness
from backend.config import settings
from backend.production_launch import run_final_launch_proof
from backend.production_smoke import run_production_smoke
import pytest


def test_objective_readiness_audits_agent_stack_platform_contract(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    audit = build_objective_readiness()
    checks = {check["key"]: check for check in audit["checks"]}

    assert audit["ok"] is True
    assert checks["promised_stack_catalog"]["ok"] is True
    assert checks["stack_execution_depth"]["details"]["min_score"] == 100
    assert checks["stack_execution_depth"]["details"]["ready_count"] == 6
    assert checks["business_outcome_routing"]["details"]["mismatches"] == {}
    assert checks["company_brain_execution_layer"]["ok"] is True
    assert checks["connector_ingestion_and_validation"]["ok"] is True
    assert checks["durable_approval_workflows"]["ok"] is True
    assert checks["business_control_plane"]["ok"] is True
    assert checks["production_proof_surface"]["ok"] is True


def test_objective_evidence_matrix_maps_business_promise_to_proof(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    matrix = build_objective_evidence_matrix(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
    )
    requirements = {item["key"]: item for item in matrix["requirements"]}

    assert matrix["code_contract_ready"] is True
    assert matrix["production_proven"] is False
    assert requirements["business_goal_to_ai_department"]["code_ok"] is True
    assert requirements["idea_to_revenue_stack"]["code_ok"] is True
    assert requirements["connector_ingestion_sync"]["status"] == "needs_live_proof"
    assert requirements["production_hardening"]["status"] == "needs_live_proof"
    assert matrix["live_proof"]["report_found"] is False
    assert matrix["live_proof"]["launch_proof_found"] is False


def test_objective_evidence_matrix_requires_aggregate_launch_proof(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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
    monkeypatch.setattr("backend.production_smoke.run_production_smoke", lambda **kwargs: {
        "ok": True,
        "created_at": "2026-05-29T00:00:00Z",
        "stack_id": kwargs["stack_id"],
        "failed_count": 0,
        "summary": "production smoke passed",
        "checks": [],
        "deploy_evidence": {"ok": True, "summary": "complete", "missing": [], "checks": []},
    })

    run_final_launch_proof(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
        live_connectors=True,
    )
    matrix = build_objective_evidence_matrix(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
    )

    assert matrix["production_proven"] is True
    assert matrix["live_proof"]["report_ok"] is True
    assert matrix["live_proof"]["manifest_verified"] is True
    assert matrix["live_proof"]["launch_proof_ok"] is True
    assert matrix["live_proof"]["launch_manifest_verified"] is True


@pytest.mark.asyncio
async def test_admin_objective_evidence_endpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from backend.api.admin import objective_evidence

    matrix = await objective_evidence(
        founder_id="founder_prod",
        stack_id="sales",
        base_url="https://api.astracreates.com",
    )

    assert matrix["founder_id"] == "founder_prod"
    assert matrix["stack_id"] == "sales"
    assert matrix["code_contract_ready"] is True


def test_production_smoke_includes_objective_readiness_gate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.platform_status.platform_status", lambda: {
        "ready": True,
        "status": "healthy",
        "checks": {
            "redis": {"ok": True, "status": "ok"},
            "models": {"ok": True, "status": "configured"},
            "company_brain_scheduler": {"ok": True, "status": "running"},
            "stack_templates": {"ok": True, "ready_templates": 6, "min_score": 100},
            "objective_readiness": {"ok": True, "status": "ready"},
            "accounts_billing": {"ok": True, "status": "ready"},
            "auth_policy": {"ok": True, "status": "ready"},
            "durable_ledgers": {"ok": True, "status": "writable"},
            "runtime": {"ok": True, "memory_percent": 12, "disk_percent": 22, "process_rss_mb": 1},
        },
        "state": {},
    })

    result = run_production_smoke()
    check = next(item for item in result["checks"] if item["key"] == "agent_stack_objective_readiness")
    evidence_check = next(item for item in result["checks"] if item["key"] == "agent_stack_objective_evidence")

    assert result["ok"] is True
    assert check["ok"] is True
    assert evidence_check["ok"] is True
