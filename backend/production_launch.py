"""One-command final production launch proof runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


def run_final_launch_proof(
    *,
    founder_id: str,
    stack_id: str = "idea_to_revenue",
    base_url: str,
    live_connectors: bool = True,
    save: bool = True,
    seed_env_connectors: bool = False,
) -> dict[str, Any]:
    """Run verification, manifest check, bundle export, and aggregate launch readiness."""
    seed_result: dict[str, Any] | None = None
    if seed_env_connectors:
        from backend.connector_setup import seed_stack_connector_credentials_from_env

        seed_result = seed_stack_connector_credentials_from_env(founder_id, stack_id)

    from backend.launch_readiness import build_launch_readiness
    from backend.production_verify import (
        export_production_verification_bundle,
        run_production_verification,
        verify_production_verification_manifest,
    )
    from backend.stack_catalog_proof import build_stack_catalog_proof

    stack_catalog_proof = build_stack_catalog_proof()
    verification = run_production_verification(
        founder_id=founder_id,
        stack_id=stack_id,
        base_url=base_url,
        live_connectors=live_connectors,
        save=True,
    )
    report_id = str(verification.get("id") or "latest")
    manifest = verify_production_verification_manifest(report_id)
    bundle = export_production_verification_bundle(report_id)
    readiness = build_launch_readiness(
        founder_id=founder_id,
        stack_id=stack_id,
        base_url=base_url,
        report_id=report_id,
    )
    ok = bool(
        stack_catalog_proof.get("ok")
        and verification.get("ok")
        and manifest.get("verified")
        and bundle.get("ok")
        and readiness.get("ok")
    )
    result = {
        "ok": ok,
        "id": _proof_id(report_id),
        "created_at": _now(),
        "founder_id": founder_id,
        "stack_id": stack_id,
        "base_url": base_url,
        "seed_env_connectors": seed_env_connectors,
        "connector_seed": seed_result,
        "stack_catalog_proof": stack_catalog_proof,
        "report_id": report_id,
        "verification": verification,
        "manifest": manifest,
        "bundle": bundle,
        "launch_readiness": readiness,
        "summary": (
            "Final Astra production launch proof passed."
            if ok
            else "Final Astra production launch proof failed; inspect verification, manifest, bundle, and launch_readiness."
        ),
    }
    if save:
        result = save_final_launch_proof(result)
    return result


def save_final_launch_proof(proof: dict[str, Any]) -> dict[str, Any]:
    """Persist the aggregate final launch proof."""
    root = _root()
    proof_id = str(proof.get("id") or _proof_id(str(proof.get("report_id") or "latest")))
    payload = {**proof, "id": proof_id}
    path = root / f"{proof_id}.json"
    latest_path = root / "latest.json"
    manifest_path = root / f"{proof_id}.sha256.json"
    latest_manifest_path = root / "latest.sha256.json"
    text = json.dumps(payload, indent=2, sort_keys=True)
    path.write_text(text)
    latest_path.write_text(text)
    manifest = _checksum_manifest(
        proof_id=proof_id,
        created_at=str(payload.get("created_at") or _now()),
        files={
            "json": path,
            "latest_json": latest_path,
        },
    )
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_path.write_text(manifest_text)
    latest_manifest_path.write_text(manifest_text)
    return {
        **payload,
        "paths": {
            **(payload.get("paths") or {}),
            "json": str(path),
            "latest_json": str(latest_path),
            "manifest": str(manifest_path),
            "latest_manifest": str(latest_manifest_path),
        },
        "evidence_manifest": manifest,
    }


def get_final_launch_proof(proof_id: str = "latest") -> dict[str, Any]:
    """Load one persisted final production launch proof."""
    safe_id = _safe_id(proof_id)
    path = _root() / ("latest.json" if safe_id == "latest" else f"{safe_id}.json")
    try:
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            return {"ok": True, "found": True, "proof": payload}
    except Exception:
        pass
    return {"ok": False, "found": False, "proof_id": proof_id, "error": "Final launch proof not found."}


def get_final_launch_proof_manifest(proof_id: str = "latest") -> dict[str, Any]:
    """Load one persisted aggregate launch proof checksum manifest."""
    safe_id = _safe_id(proof_id)
    path = _root() / ("latest.sha256.json" if safe_id == "latest" else f"{safe_id}.sha256.json")
    try:
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            return {"ok": True, "found": True, "proof_id": proof_id, "manifest": payload}
    except Exception:
        pass
    return {"ok": False, "found": False, "proof_id": proof_id, "error": "Final launch proof checksum manifest not found."}


def verify_final_launch_proof_manifest(proof_id: str = "latest") -> dict[str, Any]:
    """Recompute checksums and verify archived aggregate final launch proof files."""
    loaded = get_final_launch_proof_manifest(proof_id)
    if not loaded.get("found"):
        return {**loaded, "verified": False}
    manifest = loaded.get("manifest") or {}
    checks = []
    for key, entry in (manifest.get("files") or {}).items():
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
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        actual_bytes = path.stat().st_size
        checks.append({
            "key": key,
            "ok": actual_hash == expected_hash and actual_bytes == expected_bytes,
            "path": str(path),
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "expected_bytes": expected_bytes,
            "actual_bytes": actual_bytes,
        })
    failed = [check for check in checks if not check.get("ok")]
    verified = not failed and bool(checks)
    return {
        "ok": verified,
        "found": True,
        "verified": verified,
        "proof_id": proof_id,
        "manifest": manifest,
        "checks": checks,
        "failed": failed,
        "summary": "Final launch proof checksums match." if verified else f"Final launch proof checksum mismatch: {len(failed)} file(s).",
    }


def _root() -> Path:
    root = Path(".astra/production_launch")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _checksum_manifest(*, proof_id: str, created_at: str, files: dict[str, Path]) -> dict[str, Any]:
    return {
        "proof_id": proof_id,
        "created_at": created_at,
        "algorithm": "sha256",
        "files": {
            key: {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for key, path in files.items()
        },
    }


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in "_.-" else "_" for char in value).strip("_") or "latest"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _proof_id(report_id: str) -> str:
    return f"{_safe_id(report_id)}.launch"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete Astra production launch proof sequence.")
    parser.add_argument("--founder-id", required=True)
    parser.add_argument("--stack-id", default="idea_to_revenue")
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--live-connectors",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Validate live connector credentials. Enabled by default for final launch proof.",
    )
    parser.add_argument("--no-save", action="store_true", help="Run the final proof without persisting the aggregate launch proof JSON.")
    parser.add_argument(
        "--seed-env-connectors",
        action="store_true",
        help="Before verification, seed founder connector credentials from configured environment tokens without printing secret values.",
    )
    args = parser.parse_args()
    result = run_final_launch_proof(
        founder_id=args.founder_id,
        stack_id=args.stack_id,
        base_url=args.base_url,
        live_connectors=args.live_connectors,
        save=not args.no_save,
        seed_env_connectors=args.seed_env_connectors,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
