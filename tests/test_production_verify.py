import pytest

from backend.production_verify import (
    export_production_verification_bundle,
    get_production_verification_manifest,
    get_production_verification_markdown,
    get_production_verification_report,
    list_production_verification_reports,
    render_production_verification_markdown,
    run_production_verification,
    verify_production_verification_manifest,
)
import zipfile


def test_production_verification_persists_json_and_markdown_reports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def fake_smoke(**kwargs):
        return {
            "ok": False,
            "created_at": "2026-05-29T00:00:00Z",
            "stack_id": kwargs["stack_id"],
            "failed_count": 1,
            "summary": "production smoke failed: 1 check(s)",
            "checks": [{"key": "deploy_evidence_ready", "ok": False}],
            "deploy_evidence": {
                "ok": False,
                "summary": "Production deploy evidence missing 2 item(s) across 1 check(s).",
                "missing": ["ASTRA_CREDS_KEY", "github live provider ok"],
                "checks": [
                    {
                        "key": "credential_encryption_key",
                        "ok": False,
                        "message": "Connector credentials must be encrypted with a stable ASTRA_CREDS_KEY.",
                    }
                ],
            },
        }

    monkeypatch.setattr("backend.production_smoke.run_production_smoke", fake_smoke)

    report = run_production_verification(
        founder_id="founder_prod",
        stack_id="sales",
        base_url="https://api.astracreates.com",
        live_connectors=True,
        save=True,
    )

    assert report["ok"] is False
    assert "ASTRA_CREDS_KEY" in report["missing"]
    assert "python -m backend.production_verify" in report["verification_command"]
    assert (tmp_path / ".astra" / "production_verification" / "latest.json").exists()
    latest_md = tmp_path / ".astra" / "production_verification" / "latest.md"
    assert latest_md.exists()
    latest_manifest = tmp_path / ".astra" / "production_verification" / "latest.sha256.json"
    assert latest_manifest.exists()
    assert "## Missing Proof" in latest_md.read_text()
    assert "github live provider ok" in latest_md.read_text()

    reports = list_production_verification_reports()
    detail = get_production_verification_report(report["id"])
    markdown = get_production_verification_markdown(report["id"])
    manifest = get_production_verification_manifest(report["id"])

    assert reports["report_count"] == 1
    assert reports["latest"]["id"] == report["id"]
    assert reports["latest_ok"] is False
    assert detail["found"] is True
    assert detail["report"]["id"] == report["id"]
    assert markdown["found"] is True
    assert "# Astra Production Verification" in markdown["markdown"]
    assert "ASTRA_CREDS_KEY" in markdown["markdown"]
    assert manifest["found"] is True
    assert manifest["manifest"]["algorithm"] == "sha256"
    assert len(manifest["manifest"]["files"]["json"]["sha256"]) == 64
    assert len(manifest["manifest"]["files"]["markdown"]["sha256"]) == 64
    assert report["paths"]["latest_manifest"].endswith("latest.sha256.json")
    verified = verify_production_verification_manifest(report["id"])
    assert verified["verified"] is True
    assert verified["failed"] == []


def test_production_verification_manifest_detects_tampering(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.production_smoke.run_production_smoke", lambda **kwargs: {
        "ok": True,
        "created_at": "2026-05-29T00:00:00Z",
        "stack_id": kwargs["stack_id"],
        "failed_count": 0,
        "summary": "production smoke passed",
        "checks": [],
        "deploy_evidence": {"ok": True, "summary": "complete", "missing": [], "checks": []},
    })
    report = run_production_verification(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
        live_connectors=True,
        save=True,
    )
    markdown_path = tmp_path / report["paths"]["markdown"]
    markdown_path.write_text(markdown_path.read_text() + "\nTampered.\n")

    verified = verify_production_verification_manifest(report["id"])

    assert verified["verified"] is False
    assert any(check["key"] == "markdown" for check in verified["failed"])


def test_production_verification_bundle_contains_launch_evidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.production_smoke.run_production_smoke", lambda **kwargs: {
        "ok": True,
        "created_at": "2026-05-29T00:00:00Z",
        "stack_id": kwargs["stack_id"],
        "failed_count": 0,
        "summary": "production smoke passed",
        "checks": [],
        "deploy_evidence": {"ok": True, "summary": "complete", "missing": [], "checks": []},
    })
    report = run_production_verification(
        founder_id="founder_prod",
        stack_id="idea_to_revenue",
        base_url="https://api.astracreates.com",
        live_connectors=True,
        save=True,
    )

    bundle = export_production_verification_bundle(report["id"])

    assert bundle["ok"] is True
    assert bundle["manifest_verified"] is True
    assert bundle["filename"].endswith(".launch-evidence.zip")
    assert len(bundle["sha256"]) == 64
    with zipfile.ZipFile(bundle["path"]) as archive:
        names = set(archive.namelist())
        assert "report.json" in names
        assert "report.md" in names
        assert "sha256-manifest.json" in names
        assert "manifest-verification.json" in names
        assert "README.md" in names
        assert any(name.startswith("evidence/") for name in names)


def test_production_verification_markdown_shows_pass_state():
    markdown = render_production_verification_markdown({
        "ok": True,
        "created_at": "2026-05-29T00:00:00Z",
        "founder_id": "founder_prod",
        "stack_id": "idea_to_revenue",
        "base_url": "https://api.astracreates.com",
        "live_connectors": True,
        "verification_command": "python -m backend.production_verify --founder-id founder_prod --base-url https://api.astracreates.com",
        "missing": [],
        "next_actions": ["Archive this report as the production launch evidence."],
        "smoke": {"summary": "production smoke passed"},
        "deploy_evidence": {
            "summary": "Production deploy evidence is complete.",
            "checks": [{"key": "live_connector_evidence", "ok": True, "message": "Every required connector passed."}],
        },
    })

    assert "- Status: PASS" in markdown
    assert "- None" in markdown
    assert "Archive this report" in markdown


@pytest.mark.asyncio
async def test_admin_production_verification_endpoints(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    async def _noop():
        return None

    def fake_verify(**kwargs):
        return {
            "id": "verify_1",
            "ok": True,
            "founder_id": kwargs["founder_id"],
            "stack_id": kwargs["stack_id"],
            "base_url": kwargs["base_url"],
            "live_connectors": kwargs["live_connectors"],
            "summary": "Production verification passed.",
            "deploy_evidence": {"ok": True, "checks": []},
            "smoke": {"ok": True, "summary": "production smoke passed"},
            "missing": [],
        }

    monkeypatch.setattr("backend.production_verify.run_production_verification", fake_verify)

    from backend.api.admin import (
        production_verification,
        production_verification_report_manifest,
        production_verification_report_manifest_verify,
        production_verification_report_bundle,
        production_verification_report,
        production_verification_report_markdown,
        production_verification_reports,
    )
    from backend.production_verify import save_production_verification_report

    result = await production_verification(
        founder_id="founder_prod",
        base_url="https://api.astracreates.com",
        stack_id="sales",
        live_connectors=True,
        save=False,
    )
    save_production_verification_report({**result, "created_at": "2026-05-29T00:00:00Z"})

    reports = await production_verification_reports()
    detail = await production_verification_report("verify_1")
    markdown = await production_verification_report_markdown("verify_1")
    manifest = await production_verification_report_manifest("verify_1")
    verified = await production_verification_report_manifest_verify("verify_1")
    bundle = await production_verification_report_bundle("verify_1")

    assert result["ok"] is True
    assert reports["report_count"] == 1
    assert detail["report"]["id"] == "verify_1"
    assert markdown.media_type == "text/markdown"
    assert "Production verification passed." in markdown.body.decode()
    assert manifest["manifest"]["algorithm"] == "sha256"
    assert verified["verified"] is True
    assert bundle.media_type == "application/zip"
