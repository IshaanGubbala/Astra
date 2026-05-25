"""Cloudflare tools — DNS management, zone lookup, record creation."""
import logging
import requests
from backend.config import settings

logger = logging.getLogger(__name__)
_API = "https://api.cloudflare.com/client/v4"


def _headers():
    tok = getattr(settings, "cloudflare_api_token", "")
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"} if tok else {}


def cloudflare_get_zone(domain: str) -> dict:
    """Get Cloudflare zone ID for a domain."""
    if not _headers():
        return {"error": "CLOUDFLARE_API_TOKEN not set", "domain": domain}
    try:
        resp = requests.get(f"{_API}/zones", headers=_headers(), params={"name": domain}, timeout=10)
        zones = resp.json().get("result", [])
        if zones:
            return {"zone_id": zones[0]["id"], "domain": domain, "status": zones[0].get("status")}
        return {"error": f"Zone not found for {domain} — add domain to Cloudflare first"}
    except Exception as e:
        return {"error": str(e)}


def cloudflare_create_dns_record(domain: str, record_type: str, name: str, content: str, ttl: int = 3600, proxied: bool = False) -> dict:
    """
    Create a DNS record in Cloudflare.
    record_type: A | CNAME | TXT | MX
    name: subdomain or @ for root
    content: IP address, target domain, or TXT value
    """
    zone = cloudflare_get_zone(domain)
    if "error" in zone:
        return {**zone, "dns_record": {"type": record_type, "name": name, "content": content}}

    zone_id = zone["zone_id"]
    payload = {"type": record_type, "name": name, "content": content, "ttl": ttl, "proxied": proxied and record_type in ("A", "CNAME")}
    try:
        resp = requests.post(f"{_API}/zones/{zone_id}/dns_records", headers=_headers(), json=payload, timeout=10)
        data = resp.json()
        if data.get("success"):
            r = data["result"]
            return {"created": True, "id": r["id"], "type": r["type"], "name": r["name"], "content": r["content"]}
        return {"created": False, "errors": data.get("errors", [])}
    except Exception as e:
        return {"error": str(e)}


def cloudflare_setup_vercel_domain(domain: str, vercel_cname_target: str = "cname.vercel-dns.com") -> dict:
    """
    Wire a domain to Vercel via Cloudflare DNS.
    Adds CNAME for www and A records for root (Vercel IPs).
    """
    vercel_ips = ["76.76.21.21"]
    results = []

    # Root A record
    for ip in vercel_ips:
        results.append(cloudflare_create_dns_record(domain, "A", "@", ip, proxied=False))

    # www CNAME
    results.append(cloudflare_create_dns_record(domain, "CNAME", "www", vercel_cname_target, proxied=False))

    return {
        "domain": domain,
        "vercel_target": vercel_cname_target,
        "records_created": results,
        "next_step": f"Add {domain} in Vercel dashboard > Domains",
        "note": "Proxied=false required — Vercel needs direct connection for SSL",
    }


def cloudflare_setup_email_dns(domain: str, provider: str = "resend") -> dict:
    """
    Add email DNS records (SPF, DKIM, DMARC) for Resend or SendGrid.
    """
    records = {
        "resend": [
            {"type": "TXT", "name": "@", "content": "v=spf1 include:amazonses.com ~all"},
            {"type": "TXT", "name": f"resend._domainkey", "content": "Add DKIM value from Resend dashboard"},
            {"type": "TXT", "name": "_dmarc", "content": f"v=DMARC1; p=none; rua=mailto:dmarc@{domain}"},
        ],
        "sendgrid": [
            {"type": "CNAME", "name": "em1234", "content": "u1234567.wl1234.sendgrid.net"},
            {"type": "CNAME", "name": "s1._domainkey", "content": "s1.domainkey.u1234567.wl1234.sendgrid.net"},
            {"type": "TXT", "name": "_dmarc", "content": f"v=DMARC1; p=none; rua=mailto:dmarc@{domain}"},
        ],
    }
    provider_records = records.get(provider, records["resend"])
    results = []
    for r in provider_records:
        if "Add DKIM" not in r["content"]:
            results.append(cloudflare_create_dns_record(domain, r["type"], r["name"], r["content"]))
        else:
            results.append({"pending": True, "note": r["content"], "name": r["name"]})

    return {"domain": domain, "provider": provider, "records": results,
            "dashboard": "https://dash.cloudflare.com"}


def cloudflare_generate_instructions(domain: str) -> dict:
    """Return manual Cloudflare setup instructions when API token not configured."""
    return {
        "domain": domain,
        "steps": [
            "1. Go to https://dash.cloudflare.com and add your domain",
            "2. Update nameservers at your registrar to Cloudflare's NS records",
            "3. Wait 24-48h for propagation",
            "4. Add CLOUDFLARE_API_TOKEN to .env to enable auto-DNS management",
        ],
        "vercel_records": [
            {"type": "A", "name": "@", "value": "76.76.21.21"},
            {"type": "CNAME", "name": "www", "value": "cname.vercel-dns.com"},
        ],
        "dashboard": "https://dash.cloudflare.com",
    }
