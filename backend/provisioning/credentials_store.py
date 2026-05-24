"""Encrypted credential storage per founder in Supabase."""
import json
import os
from cryptography.fernet import Fernet

from backend.db.client import get_supabase

_KEY_ENV = "ASTRA_CREDS_KEY"


def _get_fernet() -> Fernet:
    key = os.environ.get(_KEY_ENV)
    if not key:
        # Generate and persist for this process; in prod set ASTRA_CREDS_KEY in env
        key = Fernet.generate_key().decode()
        os.environ[_KEY_ENV] = key
    return Fernet(key.encode() if isinstance(key, str) else key)


def store_credentials(founder_id: str, service: str, creds: dict) -> None:
    fernet = _get_fernet()
    encrypted = fernet.encrypt(json.dumps(creds).encode()).decode()
    get_supabase().table("founder_credentials").upsert({
        "founder_id": founder_id,
        "service": service,
        "encrypted_creds": encrypted,
    }, on_conflict="founder_id,service").execute()


def load_credentials(founder_id: str, service: str) -> dict | None:
    rows = (
        get_supabase().table("founder_credentials")
        .select("encrypted_creds")
        .eq("founder_id", founder_id)
        .eq("service", service)
        .execute()
        .data
    )
    if not rows:
        return None
    fernet = _get_fernet()
    return json.loads(fernet.decrypt(rows[0]["encrypted_creds"].encode()))


def load_all_credentials(founder_id: str) -> dict:
    """Returns {service: creds_dict} for all services this founder has connected."""
    rows = (
        get_supabase().table("founder_credentials")
        .select("service,encrypted_creds")
        .eq("founder_id", founder_id)
        .execute()
        .data
    )
    fernet = _get_fernet()
    return {
        r["service"]: json.loads(fernet.decrypt(r["encrypted_creds"].encode()))
        for r in rows
    }
