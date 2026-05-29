"""Network/deploy preflight checks before the final production proof."""

from __future__ import annotations

import argparse
import json
import socket
from typing import Any
from urllib.parse import urlparse

import requests


def build_production_preflight(
    *,
    base_url: str,
    expected_backend_ip: str = "",
    timeout: float = 8.0,
) -> dict[str, Any]:
    """Verify DNS and public HTTP surfaces required by production proof."""
    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    endpoints = ["/health", "/ready", "/metrics"]
    dns = _dns_check(host, expected_backend_ip)
    http_checks = [_http_check(base_url, path, timeout=timeout) for path in endpoints]
    failed = [check for check in [dns, *http_checks] if not check.get("ok")]
    return {
        "ok": not failed,
        "base_url": base_url,
        "host": host,
        "expected_backend_ip": expected_backend_ip,
        "checks": [dns, *http_checks],
        "failed": failed,
        "summary": (
            "Production network preflight passed."
            if not failed
            else f"Production network preflight failed: {len(failed)} check(s)."
        ),
    }


def _dns_check(host: str, expected_backend_ip: str) -> dict[str, Any]:
    if not host:
        return _check("dns_resolution", False, "Base URL must include a resolvable hostname.", {"host": host})
    try:
        resolved = sorted({
            item[4][0]
            for item in socket.getaddrinfo(host, None)
            if item and item[4]
        })
    except Exception as exc:
        return _check("dns_resolution", False, "Hostname must resolve before final proof.", {"host": host, "error": str(exc)})
    ok = bool(resolved) and (not expected_backend_ip or expected_backend_ip in resolved)
    return _check(
        "dns_resolution",
        ok,
        "Backend hostname resolves to the expected production server.",
        {
            "host": host,
            "resolved": resolved,
            "expected_backend_ip": expected_backend_ip,
        },
    )


def _http_check(base_url: str, path: str, *, timeout: float) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    try:
        response = requests.get(url, timeout=timeout)
        return _check(
            f"http_{path.strip('/')}",
            200 <= response.status_code < 400,
            f"{path} must be reachable on the public backend URL.",
            {
                "url": url,
                "status_code": response.status_code,
                "body_preview": response.text[:160],
            },
        )
    except Exception as exc:
        return _check(
            f"http_{path.strip('/')}",
            False,
            f"{path} request failed.",
            {"url": url, "error": str(exc)},
        )


def _check(key: str, ok: bool, message: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"key": key, "ok": bool(ok), "message": message, "details": details}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run production DNS and public HTTP preflight checks.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-backend-ip", default="")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()
    result = build_production_preflight(
        base_url=args.base_url,
        expected_backend_ip=args.expected_backend_ip,
        timeout=args.timeout,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
