import pytest

from backend.production_preflight import build_production_preflight


def test_production_preflight_passes_dns_and_http(monkeypatch):
    monkeypatch.setattr("backend.production_preflight.socket.getaddrinfo", lambda host, port: [
        (None, None, None, None, ("167.235.151.204", 0)),
    ])

    class Response:
        status_code = 200
        text = '{"status":"ok"}'

    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return Response()

    monkeypatch.setattr("backend.production_preflight.requests.get", fake_get)

    result = build_production_preflight(
        base_url="https://api.astracreates.com",
        expected_backend_ip="167.235.151.204",
    )

    assert result["ok"] is True
    assert result["failed"] == []
    assert calls[0][0] == "https://api.astracreates.com/health"
    assert calls[1][0] == "https://api.astracreates.com/ready"
    assert calls[2][0] == "https://api.astracreates.com/metrics"


def test_production_preflight_fails_wrong_dns(monkeypatch):
    monkeypatch.setattr("backend.production_preflight.socket.getaddrinfo", lambda host, port: [
        (None, None, None, None, ("76.76.21.21", 0)),
    ])

    class Response:
        status_code = 200
        text = "ok"

    monkeypatch.setattr("backend.production_preflight.requests.get", lambda url, timeout: Response())

    result = build_production_preflight(
        base_url="https://api.astracreates.com",
        expected_backend_ip="167.235.151.204",
    )

    assert result["ok"] is False
    assert result["failed"][0]["key"] == "dns_resolution"


def test_production_preflight_fails_http_errors(monkeypatch):
    monkeypatch.setattr("backend.production_preflight.socket.getaddrinfo", lambda host, port: [
        (None, None, None, None, ("167.235.151.204", 0)),
    ])

    def fake_get(url, timeout):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr("backend.production_preflight.requests.get", fake_get)

    result = build_production_preflight(base_url="https://api.astracreates.com")

    assert result["ok"] is False
    assert {item["key"] for item in result["failed"]} == {"http_health", "http_ready", "http_metrics"}


def test_production_preflight_treats_404_as_failure(monkeypatch):
    monkeypatch.setattr("backend.production_preflight.socket.getaddrinfo", lambda host, port: [
        (None, None, None, None, ("167.235.151.204", 0)),
    ])

    class Response:
        status_code = 404
        text = "not found"

    monkeypatch.setattr("backend.production_preflight.requests.get", lambda url, timeout: Response())

    result = build_production_preflight(base_url="https://api.astracreates.com")

    assert result["ok"] is False
    assert {item["key"] for item in result["failed"]} == {"http_health", "http_ready", "http_metrics"}


@pytest.mark.asyncio
async def test_admin_production_preflight_endpoint(monkeypatch):
    monkeypatch.setattr("backend.production_preflight.socket.getaddrinfo", lambda host, port: [
        (None, None, None, None, ("167.235.151.204", 0)),
    ])

    class Response:
        status_code = 200
        text = "ok"

    monkeypatch.setattr("backend.production_preflight.requests.get", lambda url, timeout: Response())

    from backend.api.admin import production_preflight

    result = await production_preflight(
        base_url="https://api.astracreates.com",
        expected_backend_ip="167.235.151.204",
    )

    assert result["ok"] is True
