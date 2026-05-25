"""
Supabase project auto-provisioner.
Creates a Supabase project (database + auth + storage) for a founder
using the Supabase Management API.
Falls back to setup instructions if no service_role key is configured.
"""
import logging
import time

import requests

from backend.config import settings

logger = logging.getLogger(__name__)

_SUPABASE_API = "https://api.supabase.com/v1"


def provision_supabase_project(
    founder_id: str,
    project_name: str,
    org_id: str = "",
    region: str = "us-east-1",
) -> dict:
    """
    Create a Supabase project for a founder via Management API.
    Returns connection strings, anon key, service_role key.
    """
    access_token = getattr(settings, "supabase_management_token", None)

    if not access_token:
        return _manual_setup_instructions(founder_id, project_name)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Get or use org_id
    if not org_id:
        try:
            resp = requests.get(f"{_SUPABASE_API}/organizations", headers=headers, timeout=15)
            orgs = resp.json()
            if orgs and isinstance(orgs, list):
                org_id = orgs[0]["id"]
        except Exception as e:
            logger.warning("Could not fetch Supabase orgs: %s", e)
            return _manual_setup_instructions(founder_id, project_name)

    db_password = _generate_password()
    payload = {
        "name": f"{project_name}-{founder_id[:6]}",
        "organization_id": org_id,
        "plan": "free",
        "region": region,
        "db_pass": db_password,
    }

    try:
        resp = requests.post(f"{_SUPABASE_API}/projects", headers=headers, json=payload, timeout=30)
        if resp.status_code not in (200, 201):
            logger.error("Supabase project creation failed: %s", resp.text)
            return {"created": False, "error": resp.text}

        project = resp.json()
        project_id = project.get("id", "")
        project_ref = project.get("ref", "")

        # Wait for project to be ready (up to 60s)
        ready = _wait_for_ready(project_ref, headers)
        if not ready:
            return {
                "created": True,
                "project_id": project_id,
                "ref": project_ref,
                "status": "provisioning",
                "note": "Project is provisioning. Check Supabase dashboard in 2-3 minutes.",
            }

        # Fetch API keys
        keys_resp = requests.get(
            f"{_SUPABASE_API}/projects/{project_ref}/api-keys",
            headers=headers,
            timeout=15,
        )
        keys = {k["name"]: k["api_key"] for k in (keys_resp.json() if keys_resp.ok else [])}

        return {
            "created": True,
            "project_id": project_id,
            "ref": project_ref,
            "project_url": f"https://{project_ref}.supabase.co",
            "anon_key": keys.get("anon", ""),
            "service_role_key": keys.get("service_role", ""),
            "db_password": db_password,
            "db_connection_string": f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres",
            "dashboard_url": f"https://app.supabase.com/project/{project_ref}",
            "integrations": {
                "auth": f"https://{project_ref}.supabase.co/auth/v1",
                "storage": f"https://{project_ref}.supabase.co/storage/v1",
                "realtime": f"wss://{project_ref}.supabase.co/realtime/v1",
                "rest": f"https://{project_ref}.supabase.co/rest/v1",
            },
        }

    except Exception as e:
        logger.error("Supabase provisioning failed: %s", e)
        return {"created": False, "error": str(e)}


def _wait_for_ready(project_ref: str, headers: dict, max_wait: int = 60) -> bool:
    for _ in range(max_wait // 5):
        try:
            resp = requests.get(
                f"{_SUPABASE_API}/projects/{project_ref}",
                headers=headers,
                timeout=10,
            )
            if resp.ok and resp.json().get("status") == "ACTIVE_HEALTHY":
                return True
        except Exception:
            pass
        time.sleep(5)
    return False


def _generate_password(length: int = 24) -> str:
    import secrets
    import string
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(chars) for _ in range(length))


def _manual_setup_instructions(founder_id: str, project_name: str) -> dict:
    """Return setup guide when no management API token is configured."""
    return {
        "created": False,
        "manual_setup": True,
        "instructions": [
            "1. Go to https://app.supabase.com and sign up / log in",
            f"2. Create a new project named '{project_name}'",
            "3. Copy your Project URL and anon key from Settings > API",
            "4. Add SUPABASE_URL and SUPABASE_ANON_KEY to your .env file",
            "5. (Optional) Add SUPABASE_MANAGEMENT_TOKEN to enable auto-provisioning",
        ],
        "env_keys_needed": ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"],
        "docs_url": "https://supabase.com/docs/guides/getting-started",
        "connect_endpoint": f"/setup/service — POST with service='supabase' and credentials dict",
    }
