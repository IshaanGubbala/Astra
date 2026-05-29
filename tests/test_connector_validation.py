from backend.connector_validation import validate_connector, validate_stack_connectors
from backend.provisioning.credentials_store import store_credentials


def test_connector_validation_reports_missing_required_credentials(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")

    report = validate_stack_connectors("founder_validate", "idea_to_revenue")
    github = next(item for item in report["connectors"] if item["key"] == "github")

    assert report["ready"] is False
    assert github["status"] == "missing_credentials"
    assert github["credential_status"] == "missing"
    assert "token" in github["missing_fields"]
    assert any("Add credentials for GitHub" in action for action in report["next_actions"])


def test_connector_validation_marks_saved_credentials_locally_valid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")
    store_credentials("founder_validate", "github", {"token": "ghp_test", "webhook_secret": "whsec_test"})

    github = validate_connector("founder_validate", "github", required=True)

    assert github["status"] == "locally_valid"
    assert github["credential_status"] == "valid_shape"
    assert github["webhook"]["status"] == "secured"
    assert github["provider"]["status"] == "not_checked"


def test_connector_validation_runs_mocked_live_provider_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")
    store_credentials("founder_validate", "github", {"token": "ghp_test"})

    class Response:
        status_code = 200
        text = "{}"

    calls = []

    def fake_get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return Response()

    monkeypatch.setattr("backend.connector_validation.requests.get", fake_get)

    github = validate_connector("founder_validate", "github", required=True, live=True)

    assert github["status"] == "validated"
    assert github["provider"]["status"] == "ok"
    assert calls[0][0] == "https://api.github.com/user"
    assert calls[0][1]["Authorization"] == "Bearer ghp_test"


def test_connector_validation_runs_supabase_live_provider_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")
    store_credentials("founder_validate", "supabase", {"url": "https://project.supabase.co", "service_role_key": "service_test"})

    class Response:
        status_code = 200
        text = "{}"

    calls = []

    def fake_get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return Response()

    monkeypatch.setattr("backend.connector_validation.requests.get", fake_get)

    supabase = validate_connector("founder_validate", "supabase", required=True, live=True)

    assert supabase["status"] == "validated"
    assert supabase["provider"]["status"] == "ok"
    assert calls[0][0] == "https://project.supabase.co/rest/v1/"
    assert calls[0][1]["apikey"] == "service_test"


def test_connector_validation_runs_discord_live_provider_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")
    store_credentials("founder_validate", "discord", {"bot_token": "discord_bot"})

    class Response:
        status_code = 200
        text = "{}"

    calls = []

    def fake_get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return Response()

    monkeypatch.setattr("backend.connector_validation.requests.get", fake_get)

    discord = validate_connector("founder_validate", "discord", required=True, live=True)

    assert discord["status"] == "validated"
    assert discord["provider"]["status"] == "ok"
    assert calls[0][0] == "https://discord.com/api/v10/users/@me"
    assert calls[0][1]["Authorization"] == "Bot discord_bot"


def test_connector_validation_uses_google_tokeninfo_for_live_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")
    store_credentials("founder_validate", "google_drive", {"access_token": "google_token"})

    class Response:
        status_code = 200
        text = "{}"

    calls = []

    def fake_get(url, params, timeout):
        calls.append((url, params, timeout))
        return Response()

    monkeypatch.setattr("backend.connector_validation.requests.get", fake_get)

    google_drive = validate_connector("founder_validate", "google_drive", required=True, live=True)

    assert google_drive["status"] == "validated"
    assert google_drive["provider"]["status"] == "ok"
    assert calls[0][0] == "https://www.googleapis.com/oauth2/v1/tokeninfo"
    assert calls[0][1]["access_token"] == "google_token"


def test_connector_validation_redacts_secret_values_from_provider_errors(tmp_path, monkeypatch):
    import backend.connector_validation as connector_validation

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")
    store_credentials("founder_validate", "google_drive", {"access_token": "secret_access_token"})

    def boom(_saved):
        raise RuntimeError("failed url=https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=secret_access_token")

    monkeypatch.setitem(connector_validation._LIVE_CHECKS, "google_drive", boom)

    google_drive = validate_connector("founder_validate", "google_drive", required=True, live=True)

    assert google_drive["status"] == "provider_error"
    assert "secret_access_token" not in google_drive["provider"]["detail"]
    assert "access_token=[redacted]" in google_drive["provider"]["detail"]


def test_connector_setup_plan_includes_validation_snapshot(tmp_path, monkeypatch):
    from backend.connector_setup import build_connector_setup_plan

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.provisioning.credentials_store._STORE_DIR", tmp_path / ".credentials")
    store_credentials("founder_validate", "github", {"token": "ghp_test"})
    store_credentials("founder_validate", "vercel", {"token": "vercel_test"})

    plan = build_connector_setup_plan("founder_validate", "idea_to_revenue")
    github = next(item for item in plan["connectors"] if item["key"] == "github")

    assert github["validation"]["credential_status"] == "valid_shape"
    assert github["validation"]["provider"]["status"] == "not_checked"
