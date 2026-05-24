"""
End-to-end provisioning test.
Uses a dedicated Gmail with IMAP to auto-verify accounts.

Usage:
    python tests/e2e_provision.py           # provision fresh run
    python tests/e2e_provision.py --teardown  # delete test accounts first, then provision
    python tests/e2e_provision.py --teardown-only  # just delete, don't provision
"""
import argparse
import asyncio
import sys
import time
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.config import settings


def _tag() -> str:
    return str(int(time.time()))[-6:]


def run_teardown(base_email: str, password: str):
    from backend.testing.teardown import teardown_all
    print("\n── Teardown ──")
    results = teardown_all(base_email, password)
    for svc, r in results.items():
        icon = "✓" if r.get("deleted") else "⚠"
        note = r.get("note") or r.get("error") or ""
        print(f"  {icon} {svc}: {note or 'deleted'}")


async def run_provision(email: str, password: str, founder_id: str):
    from backend.provisioning.account_provisioner import provision_all

    print(f"\n── Provisioning ──")
    print(f"  email:      {email}")
    print(f"  founder_id: {founder_id}")
    print(f"  imap:       {'✓ configured' if settings.test_email_imap_password else '✗ not set'}")
    print()

    result = await provision_all(
        founder_id=founder_id,
        email=email,
        password=password,
        base_url="http://localhost:8000",
    )

    print("── Results ──")
    for line in result.get("summary", []):
        print(f"  {line}")

    composio = result.get("composio_oauth_urls", {})
    if composio and not composio.get("error"):
        print("\n── Composio OAuth (open in browser) ──")
        for app, url in composio.items():
            if not str(url).startswith("error"):
                print(f"  {app}: {url}")

    services = result.get("services", {})
    print("\n── Service detail ──")
    for svc in ("github", "vercel", "sendgrid", "composio"):
        r = services.get(svc, {})
        created = r.get("created", False)
        token = r.get("token") or r.get("api_key") or ""
        icon = "✓" if created else "✗"
        preview = (token[:12] + "…") if token else r.get("error", r.get("note", ""))
        print(f"  {icon} {svc}: {preview}")

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--teardown", action="store_true", help="Delete test accounts first, then provision")
    parser.add_argument("--teardown-only", action="store_true", help="Only delete test accounts")
    parser.add_argument("--founder-id", default=None, help="Founder ID to use (default: test_<tag>)")
    parser.add_argument("--password", default="AstraTest2024!", help="Password for all provisioned accounts")
    args = parser.parse_args()

    base_email = settings.test_email_base
    if not base_email:
        print("ERROR: TEST_EMAIL_BASE not set in .env")
        sys.exit(1)

    password = args.password
    tag = _tag()
    # Gmail + aliases: all mail routes to base inbox, services see unique addresses
    local, domain = base_email.split("@")
    test_email = f"{local}+run{tag}@{domain}"
    founder_id = args.founder_id or f"test_{tag}"

    if args.teardown or args.teardown_only:
        run_teardown(base_email, password)
        if args.teardown_only:
            return

    asyncio.run(run_provision(test_email, password, founder_id))


if __name__ == "__main__":
    main()
