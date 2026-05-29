from pathlib import Path

from backend.production_requirements import build_production_requirements


def test_production_launch_runbook_covers_current_gate_contract():
    text = Path("docs/Production_Launch_Runbook.md").read_text()
    requirements = build_production_requirements(
        founder_id="<prod_founder>",
        stack_id="idea_to_revenue",
        base_url="$BACKEND_URL",
    )

    assert "/admin/production-requirements" in text
    assert "/admin/objective" in text
    assert "/admin/objective/evidence" in text
    assert "/admin/stack-catalog-proof" in text
    assert "/admin/launch-readiness" in text
    assert "stack catalog proof" in text.lower()
    assert "python -m backend.launch_readiness" in text
    assert "/admin/production-verification" in text
    assert "/admin/production-launch" in text
    assert "/admin/production-launch/reports/latest" in text
    assert "/admin/production-verification/reports/latest/markdown" in text
    assert "/admin/production-verification/reports/latest/manifest" in text
    assert "/admin/production-verification/reports/latest/manifest/verify" in text
    assert "/admin/production-verification/reports/latest/bundle" in text
    assert "Verify manifest" in text
    assert "Download proof bundle" in text
    assert "python -m backend.production_verify" in text
    assert "python -m backend.production_launch" in text
    assert "python -m backend.production_env" in text
    assert "deploy/server-preflight.sh" in text
    assert "deploy/production-env-missing.sh" in text
    assert "deploy/production-proof.sh" in text
    assert "--live-connectors" in text
    assert "Live connector validation is enabled by default" in text
    assert "--verify-manifest" in text
    assert "--export-bundle" in text
    assert "code_contract_ready=true" in text
    assert "ok=true" in text
    for artifact in requirements["final_gate"]["writes"]:
        assert artifact in text
    assert ".astra/production_verification/latest.sha256.json" in text
    assert ".astra/production_launch/latest.json" in text
    for key in ["ASTRA_CREDS_KEY", "ASTRA_PLATFORM_ADMINS", "STRIPE_WEBHOOK_SECRET"]:
        assert key in text


def test_production_proof_script_runs_all_required_gates_in_order():
    text = Path("deploy/production-proof.sh").read_text()

    assert text.startswith("#!/bin/bash")
    assert "set -euo pipefail" in text
    assert "BACKEND_URL=${BACKEND_URL:?" in text
    expected_order = [
        "backend.production_bootstrap",
        "backend.production_preflight",
        "backend.launch_readiness",
        "backend.production_launch",
    ]
    positions = [text.index(item) for item in expected_order]
    assert positions == sorted(positions)
    assert "--live-connectors" in text
    assert "--seed-env-connectors" in text


def test_server_preflight_script_checks_deploy_state_without_printing_secrets():
    text = Path("deploy/server-preflight.sh").read_text()

    assert text.startswith("#!/bin/bash")
    assert "set -euo pipefail" in text
    assert "backend.production_env" in text
    assert "docker compose ps" in text
    assert "http://127.0.0.1:8000/health" in text
    assert "http://127.0.0.1:8000/ready" in text
    assert "http://127.0.0.1:8000/metrics" in text
    assert "backend.production_preflight" in text
    assert "backend.production_bootstrap" in text
    assert "missing_env_placeholders_begin" in text
    assert "cut -d= -f2-" not in text
    assert "cat .env" not in text


def test_production_env_missing_script_outputs_placeholders_not_values():
    text = Path("deploy/production-env-missing.sh").read_text()

    assert text.startswith("#!/bin/bash")
    assert "set -euo pipefail" in text
    assert "backend.production_env" in text
    assert "--print-missing-template" in text
    assert "cat .env" not in text
