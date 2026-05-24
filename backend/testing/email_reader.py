"""
IMAP reader for auto-verifying accounts during provisioning.
Connects to Gmail, polls for verification emails, returns clickable URLs.
"""
import email as email_lib
import imaplib
import logging
import re
import time

logger = logging.getLogger(__name__)

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

VERIFICATION_SENDERS = {
    "github": ["github.com", "noreply@github.com"],
    "sendgrid": ["sendgrid.com", "twilio.com"],
    "composio": ["composio.dev", "composio.io"],
    "vercel": ["vercel.com"],
}


def wait_for_verification_url(
    email_address: str,
    imap_password: str,
    service: str,
    timeout: int = 120,
    poll_interval: int = 5,
) -> str | None:
    """
    Poll inbox until a verification email from `service` arrives.
    Returns the verification URL or None on timeout.
    """
    password = imap_password.replace(" ", "")
    senders = VERIFICATION_SENDERS.get(service, [service])
    deadline = time.time() + timeout

    logger.info("Waiting for %s verification email (timeout=%ds)…", service, timeout)

    while time.time() < deadline:
        try:
            url = _check_inbox(email_address, password, senders)
            if url:
                logger.info("Found %s verification URL: %s", service, url[:80])
                return url
        except Exception as e:
            logger.debug("IMAP poll error: %s", e)
        time.sleep(poll_interval)

    logger.warning("Timed out waiting for %s verification email", service)
    return None


def _check_inbox(email_address: str, password: str, senders: list[str]) -> str | None:
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    try:
        mail.login(email_address, password)
        mail.select("inbox")

        # Search all unseen mail — check newest first
        _, data = mail.search(None, "UNSEEN")
        mail_ids = data[0].split()

        for mid in reversed(mail_ids):
            _, msg_data = mail.fetch(mid, "(RFC822)")
            msg = email_lib.message_from_bytes(msg_data[0][1])

            from_hdr = msg.get("From", "").lower()
            subject = msg.get("Subject", "").lower()
            combined = from_hdr + " " + subject

            if not any(s.lower() in combined for s in senders):
                continue

            body = _extract_body(msg)
            url = _find_verification_url(body)
            if url:
                # Mark as read so we don't re-process
                mail.store(mid, "+FLAGS", "\\Seen")
                return url

    finally:
        try:
            mail.logout()
        except Exception:
            pass
    return None


def _extract_body(msg) -> str:
    parts = []
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct in ("text/plain", "text/html"):
                try:
                    parts.append(part.get_payload(decode=True).decode("utf-8", errors="ignore"))
                except Exception:
                    pass
    else:
        try:
            parts.append(msg.get_payload(decode=True).decode("utf-8", errors="ignore"))
        except Exception:
            pass
    return "\n".join(parts)


def _find_verification_url(body: str) -> str | None:
    keywords = ["verify", "confirm", "activate", "validate", "email", "account"]
    urls = re.findall(r'https?://[^\s<>"\')\]]+', body)
    for url in urls:
        url_lower = url.lower()
        if any(kw in url_lower for kw in keywords):
            # Strip trailing punctuation
            url = re.sub(r'[.,;!?\'"]+$', '', url)
            return url
    return None
