from backend.config import settings
from backend.production_smoke import list_smoke_reports, run_production_smoke


def _healthy_status() -> dict:
    return {
        "ready": True,
        "status": "healthy",
        "checks": {
            "redis": {"ok": True, "status": "ok"},
            "models": {"ok": True, "status": "configured"},
            "company_brain_scheduler": {"ok": True, "status": "running"},
            "stack_templates": {"ok": True, "ready_templates": 6, "min_score": 100},
            "accounts_billing": {"ok": True, "status": "ready"},
            "auth_policy": {"ok": True, "status": "ready"},
            "durable_ledgers": {"ok": True, "status": "writable"},
            "runtime": {"ok": True, "memory_percent": 12, "disk_percent": 22, "process_rss_mb": 1},
        },
        "state": {
            "sessions_active": 0,
            "sessions_completed": 0,
            "events_buffered": 0,
            "workflow_snapshots": 0,
            "approval_ledgers": 0,
            "company_brains": 0,
            "runs_error": 0,
            "connector_sources_error": 0,
        },
    }


def test_production_smoke_passes_with_healthy_platform(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.production_smoke.platform_status", lambda: _healthy_status(), raising=False)
    monkeypatch.setattr("backend.platform_status.platform_status", lambda: _healthy_status())

    result = run_production_smoke()

    assert result["ok"] is True
    assert result["failed_count"] == 0
    assert any(check["key"] == "stack_catalog_execution_packages" for check in result["checks"])
    assert result["stack_catalog_proof"]["ok"] is True
    assert any(check["key"] == "alerting_operational" for check in result["checks"])


def test_production_smoke_strict_requires_billing_and_alert_delivery(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.platform_status.platform_status", lambda: _healthy_status())
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    monkeypatch.setattr(settings, "stripe_price_starter", "")
    monkeypatch.setattr(settings, "stripe_price_team", "")
    monkeypatch.setattr(settings, "stripe_price_scale", "")
    monkeypatch.setattr(settings, "astra_alert_webhook_url", "")

    result = run_production_smoke(strict=True)
    failed_keys = {check["key"] for check in result["checks"] if not check["ok"]}

    assert result["ok"] is False
    assert "billing_self_serve_configured" in failed_keys
    assert "alert_delivery_configured" in failed_keys
    assert "strict_base_url_provided" in failed_keys
    assert "strict_founder_id_provided" in failed_keys
    assert "strict_live_connectors_requested" in failed_keys


def test_production_smoke_strict_requires_real_connector_proof(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.platform_status.platform_status", lambda: _healthy_status())
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test")
    monkeypatch.setattr(settings, "stripe_price_starter", "price_starter")
    monkeypatch.setattr(settings, "stripe_price_team", "price_team")
    monkeypatch.setattr(settings, "stripe_price_scale", "price_scale")
    monkeypatch.setattr(settings, "astra_alert_webhook_url", "https://hooks.example/astra")

    class Response:
        status_code = 200
        text = "ok"

    monkeypatch.setattr("backend.production_smoke.requests.get", lambda url, timeout: Response())
    monkeypatch.setattr("backend.connector_validation.validate_stack_connectors", lambda founder_id, stack_id, live=False: {
        "ready": True,
        "live": live,
        "connectors": [{"key": "github", "required": True, "provider": {"status": "not_checked"}}],
    })

    result = run_production_smoke(
        strict=True,
        base_url="https://astra.example",
        founder_id="founder_smoke",
        stack_id="idea_to_revenue",
        live_connectors=False,
    )
    failed_keys = {check["key"] for check in result["checks"] if not check["ok"]}

    assert result["ok"] is False
    assert "strict_live_connectors_requested" in failed_keys
    assert "connector_live_validation" in failed_keys


def test_production_smoke_strict_rejects_unsupported_required_connector(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.platform_status.platform_status", lambda: _healthy_status())
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test")
    monkeypatch.setattr(settings, "stripe_price_starter", "price_starter")
    monkeypatch.setattr(settings, "stripe_price_team", "price_team")
    monkeypatch.setattr(settings, "stripe_price_scale", "price_scale")
    monkeypatch.setattr(settings, "astra_alert_webhook_url", "https://hooks.example/astra")

    class Response:
        status_code = 200
        text = "ok"

    monkeypatch.setattr("backend.production_smoke.requests.get", lambda url, timeout: Response())
    monkeypatch.setattr("backend.connector_validation.validate_stack_connectors", lambda founder_id, stack_id, live=False: {
        "ready": True,
        "live": live,
        "connectors": [{"key": "crm", "required": True, "provider": {"status": "unsupported"}}],
    })

    result = run_production_smoke(
        strict=True,
        base_url="https://astra.example",
        founder_id="founder_smoke",
        stack_id="idea_to_revenue",
        live_connectors=True,
    )
    connector_check = next(check for check in result["checks"] if check["key"] == "connector_live_validation")

    assert result["ok"] is False
    assert connector_check["ok"] is False
    assert connector_check["details"]["failed_required"][0]["key"] == "crm"


def test_production_smoke_http_checks_report_server_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.platform_status.platform_status", lambda: _healthy_status())

    class Response:
        def __init__(self, status_code: int, text: str = ""):
            self.status_code = status_code
            self.text = text

    def fake_get(url, timeout):
        if url.endswith("/ready"):
            return Response(503, "not ready")
        return Response(200, "ok")

    monkeypatch.setattr("backend.production_smoke.requests.get", fake_get)

    result = run_production_smoke(base_url="https://astra.example")
    http_ready = next(check for check in result["checks"] if check["key"] == "http_ready")

    assert result["ok"] is False
    assert http_ready["ok"] is False
    assert http_ready["details"]["status_code"] == 503


def test_production_smoke_persists_deploy_evidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.platform_status.platform_status", lambda: _healthy_status())

    result = run_production_smoke(save=True, stack_id="sales")
    reports = list_smoke_reports()

    assert result["id"]
    assert result["created_at"]
    assert reports["report_count"] == 1
    assert reports["latest"]["id"] == result["id"]
    assert reports["latest_ok"] is True
    assert (tmp_path / ".astra" / "production_smoke" / "latest.json").exists()
