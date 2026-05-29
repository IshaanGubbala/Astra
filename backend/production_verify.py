"""Operator workflow for final production verification.

This wraps strict smoke into a durable JSON + Markdown report so the final
launch gate is repeatable and readable by non-engineering operators.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import zipfile
from pathlib import Path
from typing import Any


def run_production_verification(
    *,
    founder_id: str,
    stack_id: str = "idea_to_revenue",
    base_url: str,
    live_connectors: bool = True,
    save: bool = True,
) -> dict[str, Any]:
    """Run the final production gate and optionally persist operator reports."""
    from backend.production_smoke import run_production_smoke

    smoke = run_production_smoke(
        founder_id=founder_id,
        stack_id=stack_id,
        live_connectors=live_connectors,
        base_url=base_url,
        strict=True,
        save=save,
    )
    evidence = smoke.get("deploy_evidence") or {}
    report = {
        "id": _report_id(smoke),
        "ok": bool(smoke.get("ok") and evidence.get("ok")),
        "created_at": smoke.get("created_at") or _now(),
        "founder_id": founder_id,
        "stack_id": stack_id,
        "base_url": base_url,
        "live_connectors": live_connectors,
        "summary": _summary(smoke, evidence),
        "smoke": smoke,
        "deploy_evidence": evidence,
        "missing": evidence.get("missing", []),
        "next_actions": _next_actions(smoke, evidence),
        "verification_command": _verification_command(founder_id, stack_id, base_url, live_connectors),
    }
    if save:
        report = save_production_verification_report(report)
    return report


def save_production_verification_report(report: dict[str, Any]) -> dict[str, Any]:
    """Persist JSON and Markdown copies of the production verification report."""
    root = _root()
    report_id = str(report.get("id") or _report_id(report))
    payload = {**report, "id": report_id}
    json_path = root / f"{report_id}.json"
    markdown_path = root / f"{report_id}.md"
    latest_json_path = root / "latest.json"
    latest_markdown_path = root / "latest.md"
    manifest_path = root / f"{report_id}.sha256.json"
    latest_manifest_path = root / "latest.sha256.json"
    json_text = json.dumps(payload, indent=2, sort_keys=True)
    markdown_text = render_production_verification_markdown(payload)
    json_path.write_text(json_text)
    markdown_path.write_text(markdown_text)
    latest_json_path.write_text(json_text)
    latest_markdown_path.write_text(markdown_text)
    manifest = _checksum_manifest(
        report_id=report_id,
        created_at=str(payload.get("created_at") or _now()),
        files={
            "json": json_path,
            "markdown": markdown_path,
            "latest_json": latest_json_path,
            "latest_markdown": latest_markdown_path,
        },
    )
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_path.write_text(manifest_text)
    latest_manifest_path.write_text(manifest_text)
    return {
        **payload,
        "paths": {
            "json": str(json_path),
            "markdown": str(markdown_path),
            "manifest": str(manifest_path),
            "latest_json": str(latest_json_path),
            "latest_markdown": str(latest_markdown_path),
            "latest_manifest": str(latest_manifest_path),
        },
        "evidence_manifest": manifest,
    }


def list_production_verification_reports(limit: int = 20) -> dict[str, Any]:
    """List persisted final production verification reports."""
    reports: list[dict[str, Any]] = []
    for path in sorted(_root().glob("*.json"), reverse=True):
        if path.name == "latest.json" or path.name.endswith(".sha256.json"):
            continue
        try:
            reports.append(json.loads(path.read_text()))
        except Exception:
            continue
    reports.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    latest = reports[0] if reports else _read_json(_root() / "latest.json")
    bounded = max(1, min(limit, 100))
    return {
        "reports": reports[:bounded],
        "report_count": len(reports),
        "latest": latest,
        "latest_ok": bool(latest.get("ok")) if latest else False,
    }


def get_production_verification_report(report_id: str = "latest") -> dict[str, Any]:
    """Load one persisted production verification report."""
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", report_id).strip("_") or "latest"
    path = _root() / ("latest.json" if safe_id == "latest" else f"{safe_id}.json")
    payload = _read_json(path)
    if not payload:
        return {"ok": False, "found": False, "report_id": report_id, "error": "Production verification report not found."}
    return {"ok": True, "found": True, "report": payload}


def get_production_verification_markdown(report_id: str = "latest") -> dict[str, Any]:
    """Load a persisted Markdown report, regenerating from JSON if needed."""
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", report_id).strip("_") or "latest"
    root = _root()
    markdown_path = root / ("latest.md" if safe_id == "latest" else f"{safe_id}.md")
    try:
        markdown = markdown_path.read_text()
        if markdown.strip():
            return {"ok": True, "found": True, "report_id": report_id, "markdown": markdown}
    except Exception:
        pass

    loaded = get_production_verification_report(report_id)
    if not loaded.get("found"):
        return {"ok": False, "found": False, "report_id": report_id, "error": "Production verification Markdown report not found."}
    markdown = render_production_verification_markdown(loaded.get("report") or {})
    return {"ok": True, "found": True, "report_id": report_id, "markdown": markdown, "regenerated": True}


def get_production_verification_manifest(report_id: str = "latest") -> dict[str, Any]:
    """Load one persisted checksum manifest."""
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", report_id).strip("_") or "latest"
    path = _root() / ("latest.sha256.json" if safe_id == "latest" else f"{safe_id}.sha256.json")
    payload = _read_json(path)
    if not payload:
        return {"ok": False, "found": False, "report_id": report_id, "error": "Production verification checksum manifest not found."}
    return {"ok": True, "found": True, "manifest": payload}


def verify_production_verification_manifest(report_id: str = "latest") -> dict[str, Any]:
    """Recompute checksums and verify archived production evidence files."""
    loaded = get_production_verification_manifest(report_id)
    if not loaded.get("found"):
        return {**loaded, "verified": False}
    manifest = loaded.get("manifest") or {}
    files = manifest.get("files") or {}
    checks = []
    for key, entry in files.items():
        path = Path(str(entry.get("path") or ""))
        expected_hash = str(entry.get("sha256") or "")
        expected_bytes = int(entry.get("bytes") or 0)
        if not path.exists():
            checks.append({
                "key": key,
                "ok": False,
                "path": str(path),
                "error": "missing_file",
                "expected_sha256": expected_hash,
            })
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        actual_bytes = path.stat().st_size
        checks.append({
            "key": key,
            "ok": actual == expected_hash and actual_bytes == expected_bytes,
            "path": str(path),
            "expected_sha256": expected_hash,
            "actual_sha256": actual,
            "expected_bytes": expected_bytes,
            "actual_bytes": actual_bytes,
        })
    failed = [check for check in checks if not check.get("ok")]
    return {
        "ok": not failed and bool(checks),
        "found": True,
        "verified": not failed and bool(checks),
        "report_id": report_id,
        "manifest": manifest,
        "checks": checks,
        "failed": failed,
        "summary": "Production verification evidence checksums match." if not failed and checks else f"Production verification evidence checksum mismatch: {len(failed)} file(s).",
    }


def export_production_verification_bundle(report_id: str = "latest") -> dict[str, Any]:
    """Create a ZIP bundle containing report, Markdown proof, manifest, and verification result."""
    loaded = get_production_verification_report(report_id)
    if not loaded.get("found"):
        return {"ok": False, "found": False, "report_id": report_id, "error": "Production verification report not found."}
    manifest = get_production_verification_manifest(report_id)
    if not manifest.get("found"):
        return {"ok": False, "found": False, "report_id": report_id, "error": "Production verification checksum manifest not found."}

    verification = verify_production_verification_manifest(report_id)
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", report_id).strip("_") or "latest"
    report = loaded.get("report") or {}
    resolved_id = str(report.get("id") or safe_id)
    root = _root()
    bundle_name = f"{resolved_id}.launch-evidence.zip"
    bundle_path = root / bundle_name
    markdown = get_production_verification_markdown(report_id)

    files = (manifest.get("manifest") or {}).get("files") or {}
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for key, entry in files.items():
            path = Path(str(entry.get("path") or ""))
            if path.exists():
                archive.write(path, arcname=f"evidence/{key}{path.suffix}")
        archive.writestr("report.json", json.dumps(report, indent=2, sort_keys=True))
        archive.writestr("report.md", str(markdown.get("markdown") or render_production_verification_markdown(report)))
        archive.writestr("sha256-manifest.json", json.dumps(manifest.get("manifest") or {}, indent=2, sort_keys=True))
        archive.writestr("manifest-verification.json", json.dumps(verification, indent=2, sort_keys=True))
        archive.writestr("README.md", _bundle_readme(report, verification))

    return {
        "ok": bool(verification.get("verified")),
        "found": True,
        "report_id": resolved_id,
        "path": str(bundle_path),
        "filename": bundle_name,
        "bytes": bundle_path.stat().st_size,
        "sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
        "manifest_verified": bool(verification.get("verified")),
        "summary": (
            "Production launch evidence bundle created and checksum verified."
            if verification.get("verified")
            else "Production launch evidence bundle created, but source manifest verification failed."
        ),
    }


def render_production_verification_markdown(report: dict[str, Any]) -> str:
    """Render a concise operator-facing verification summary."""
    evidence = report.get("deploy_evidence") or {}
    smoke = report.get("smoke") or {}
    checks = evidence.get("checks", [])
    lines = [
        "# Astra Production Verification",
        "",
        f"- Status: {'PASS' if report.get('ok') else 'FAIL'}",
        f"- Created: {report.get('created_at') or ''}",
        f"- Stack: {report.get('stack_id') or ''}",
        f"- Founder workspace: {report.get('founder_id') or ''}",
        f"- Base URL: {report.get('base_url') or ''}",
        f"- Live connectors: {bool(report.get('live_connectors'))}",
        f"- Summary: {report.get('summary') or ''}",
        f"- Smoke summary: {smoke.get('summary') or ''}",
        f"- Deploy evidence: {evidence.get('summary') or ''}",
        "",
        "## Exact Command",
        "",
        f"```bash\n{report.get('verification_command') or ''}\n```",
        "",
        "## Missing Proof",
        "",
    ]
    missing = report.get("missing") or []
    if missing:
        lines.extend([f"- {item}" for item in missing])
    else:
        lines.append("- None")
    lines.extend(["", "## Next Actions", ""])
    actions = report.get("next_actions") or []
    if actions:
        lines.extend([f"- {item}" for item in actions])
    else:
        lines.append("- None")
    lines.extend(["", "## Evidence Checks", ""])
    for check in checks:
        status = "PASS" if check.get("ok") else "FAIL"
        lines.append(f"- {status}: {check.get('key')} - {check.get('message')}")
    return "\n".join(lines).rstrip() + "\n"


def _bundle_readme(report: dict[str, Any], verification: dict[str, Any]) -> str:
    status = "PASS" if report.get("ok") else "FAIL"
    checksum = "VERIFIED" if verification.get("verified") else "FAILED"
    return "\n".join([
        "# Astra Production Launch Evidence Bundle",
        "",
        f"- Report ID: {report.get('id') or ''}",
        f"- Status: {status}",
        f"- Stack: {report.get('stack_id') or ''}",
        f"- Founder workspace: {report.get('founder_id') or ''}",
        f"- Base URL: {report.get('base_url') or ''}",
        f"- Live connectors: {bool(report.get('live_connectors'))}",
        f"- Checksum manifest: {checksum}",
        "",
        "Contents:",
        "",
        "- `report.json`: full machine-readable verification report.",
        "- `report.md`: operator-readable launch proof.",
        "- `sha256-manifest.json`: original evidence checksum manifest.",
        "- `manifest-verification.json`: recomputed checksum verification result.",
        "- `evidence/`: persisted source evidence files.",
        "",
    ])


def _next_actions(smoke: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    actions = []
    missing = evidence.get("missing", [])
    if missing:
        actions.append("Configure the missing production env/connector proof listed above, then rerun the exact command.")
    failed_smoke = [item.get("key") for item in smoke.get("checks", []) if not item.get("ok")]
    if failed_smoke:
        actions.append(f"Resolve failed smoke checks: {', '.join(str(item) for item in failed_smoke[:12])}.")
    if not missing and not failed_smoke:
        actions.append("Archive this report as the production launch evidence.")
    return actions


def _summary(smoke: dict[str, Any], evidence: dict[str, Any]) -> str:
    if smoke.get("ok") and evidence.get("ok"):
        return "Production verification passed."
    missing_count = len(evidence.get("missing", []))
    failed_count = int(smoke.get("failed_count") or 0)
    return f"Production verification failed: {failed_count} smoke check(s), {missing_count} missing deploy evidence item(s)."


def _verification_command(founder_id: str, stack_id: str, base_url: str, live_connectors: bool) -> str:
    parts = [
        "python -m backend.production_verify",
        f"--founder-id {founder_id}",
        f"--stack-id {stack_id}",
        f"--base-url {base_url}",
    ]
    if live_connectors:
        parts.append("--live-connectors")
    return " ".join(parts)


def _root() -> Path:
    root = Path(".astra/production_verification")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _checksum_manifest(*, report_id: str, created_at: str, files: dict[str, Path]) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "created_at": created_at,
        "algorithm": "sha256",
        "files": {
            key: {
                "path": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for key, path in files.items()
        },
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _report_id(report: dict[str, Any]) -> str:
    base = f"{report.get('created_at') or _now()}-{report.get('stack_id') or 'stack'}-{'ok' if report.get('ok') else 'fail'}"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", base).strip("_")[:160] or "production_verification"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run final Astra production verification and write operator reports.")
    parser.add_argument("--founder-id", default="")
    parser.add_argument("--stack-id", default="idea_to_revenue")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--live-connectors", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--report-id", default="latest", help="Report id for --verify-manifest or --export-bundle.")
    parser.add_argument("--verify-manifest", action="store_true", help="Verify an existing production evidence checksum manifest.")
    parser.add_argument("--export-bundle", action="store_true", help="Create a launch evidence ZIP bundle for an existing report.")
    args = parser.parse_args()
    if args.verify_manifest:
        result = verify_production_verification_manifest(args.report_id)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("verified") else 1
    if args.export_bundle:
        result = export_production_verification_bundle(args.report_id)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1
    if not args.founder_id or not args.base_url:
        parser.error("--founder-id and --base-url are required unless --verify-manifest or --export-bundle is used.")
    report = run_production_verification(
        founder_id=args.founder_id,
        stack_id=args.stack_id,
        base_url=args.base_url,
        live_connectors=args.live_connectors,
        save=not args.no_save,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
