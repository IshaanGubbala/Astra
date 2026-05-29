from pathlib import Path

from backend.production_env import (
    AUTH_SOURCE_ENV,
    REQUIRED_PRODUCTION_ENV,
    audit_env_file,
    render_missing_env_template,
)


def test_production_env_audit_reports_status_without_values(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "BACKEND_URL=https://api.astracreates.com",
                "FRONTEND_URL=https://astracreates.com",
                "ASTRA_REQUIRE_AUTH=true",
                "ASTRA_PLATFORM_ADMINS=admin_secret_user",
                "ASTRA_JWT_SECRET=super_secret_jwt",
                "ASTRA_CREDS_KEY=very_secret_creds",
                "STRIPE_SECRET_KEY=sk_live_secret",
            ]
        )
    )

    result = audit_env_file(env_file)
    rendered = str(result)

    assert result["env_file_exists"] is True
    assert "ASTRA_ALERT_WEBHOOK_URL" in result["missing"]
    assert result["auth_source_configured"] is True
    assert "admin_secret_user" not in rendered
    assert "super_secret_jwt" not in rendered
    assert "very_secret_creds" not in rendered
    assert "sk_live_secret" not in rendered


def test_production_env_template_only_outputs_missing_keys(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "BACKEND_URL=https://api.astracreates.com",
                "ASTRA_CREDS_KEY=do_not_print",
                "ASTRA_TRUST_AUTH_HEADERS=true",
            ]
        )
    )

    template = render_missing_env_template(env_file)

    assert "BACKEND_URL=" not in template
    assert "ASTRA_CREDS_KEY=" not in template
    assert "do_not_print" not in template
    assert "FRONTEND_URL=https://astracreates.com" in template
    assert "ASTRA_JWT_SECRET=" not in template
    assert "# Set one auth source:" not in template


def test_production_env_accepts_any_auth_source(tmp_path: Path):
    for key, value in [
        ("ASTRA_JWT_JWKS_URL", "https://issuer.example/.well-known/jwks.json"),
        ("ASTRA_JWT_SECRET", "secret"),
        ("ASTRA_TRUST_AUTH_HEADERS", "true"),
    ]:
        env_file = tmp_path / f"{key}.env"
        body = [f"{env_key}=configured" for env_key in REQUIRED_PRODUCTION_ENV]
        body.extend(f"{env_key}=" for env_key in AUTH_SOURCE_ENV)
        body.append(f"{key}={value}")
        env_file.write_text("\n".join(body))

        result = audit_env_file(env_file)

        assert result["auth_source_configured"] is True
        assert result["ok"] is True


def test_production_env_missing_file_is_safe(tmp_path: Path):
    missing_file = tmp_path / "missing.env"

    result = audit_env_file(missing_file)
    template = render_missing_env_template(missing_file)

    assert result["ok"] is False
    assert result["env_file_exists"] is False
    assert set(result["missing"]) == set(REQUIRED_PRODUCTION_ENV)
    assert "ASTRA_JWT_SECRET=" in template
    assert "STRIPE_SECRET_KEY=" in template
