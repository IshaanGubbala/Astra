"""
Headless browser provisioner.
Creates GitHub, Vercel, SendGrid accounts with founder email+password,
extracts API tokens, returns them.
"""
import logging
import secrets
import time

logger = logging.getLogger(__name__)


def provision_github(email: str, password: str, username: str = None) -> dict:
    """
    Create GitHub account + personal access token.
    Returns {"token": "ghp_...", "username": "...", "created": bool}
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    username = username or _slug(email)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = ctx.new_page()

        try:
            # --- Sign up ---
            page.goto("https://github.com/signup", timeout=30000)
            page.fill("input#email", email)
            page.click("button[type=submit]")
            page.wait_for_timeout(1000)

            page.fill("input#password", password)
            page.click("button[type=submit]")
            page.wait_for_timeout(1000)

            page.fill("input#login", username)
            page.click("button[type=submit]")
            page.wait_for_timeout(2000)

            # Email verification required — check if we landed on verify page
            if "verify" in page.url or "email" in page.url:
                logger.info("GitHub requires email verification for %s", email)
                browser.close()
                return {
                    "token": None,
                    "username": username,
                    "created": False,
                    "needs_verification": True,
                    "note": "GitHub sent a verification email to %s. Verify then reconnect." % email,
                }

            # --- Try to login if account already exists ---
            page.goto("https://github.com/login", timeout=30000)
            page.fill("input#login_field", email)
            page.fill("input#password", password)
            page.click("input[type=submit]")
            page.wait_for_timeout(2000)

            if "github.com" not in page.url or "login" in page.url:
                browser.close()
                return {"token": None, "created": False, "error": "Login failed"}

            # Get username from profile
            profile_resp = page.evaluate("() => fetch('/api/v3/user').then(r=>r.json())")
            # Simpler: read from nav
            actual_username = page.locator("[data-login]").first.get_attribute("data-login") or username

            # --- Create personal access token ---
            page.goto("https://github.com/settings/tokens/new", timeout=30000)
            page.fill("input#oauth_access[name='oauth_access[description]']", "Astra Automation Token")
            # Select all repos scope
            page.check("input#repo")
            # Set no expiration
            page.select_option("select#oauth_access_expires_at", "0")
            page.click("button[type=submit]")
            page.wait_for_timeout(2000)

            token_el = page.locator("code#new-oauth-token")
            token = token_el.text_content() if token_el.count() > 0 else None

            browser.close()
            return {
                "token": token,
                "username": actual_username,
                "created": True,
                "note": "Token has full repo access." if token else "Token extraction failed — create manually at github.com/settings/tokens",
            }

        except PWTimeout as e:
            logger.error("GitHub provisioning timed out: %s", e)
            browser.close()
            return {"token": None, "created": False, "error": "Timeout: %s" % str(e)}
        except Exception as e:
            logger.error("GitHub provisioning failed: %s", e)
            try:
                browser.close()
            except Exception:
                pass
            return {"token": None, "created": False, "error": str(e)}


def provision_vercel(email: str, password: str, github_token: str = None) -> dict:
    """
    Sign into Vercel (via GitHub OAuth or email) and extract API token.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        try:
            page.goto("https://vercel.com/login", timeout=30000)

            if github_token:
                # Continue with GitHub
                page.click("button:has-text('Continue with GitHub')")
                page.wait_for_timeout(3000)
                # GitHub OAuth redirect
                if "github.com" in page.url:
                    page.fill("input#login_field", email)
                    page.fill("input#password", password)
                    page.click("input[type=submit]")
                    page.wait_for_timeout(2000)
                    # Authorize if prompted
                    auth_btn = page.locator("button:has-text('Authorize')")
                    if auth_btn.count() > 0:
                        auth_btn.click()
                        page.wait_for_timeout(2000)
            else:
                page.click("button:has-text('Continue with Email')")
                page.fill("input[type=email]", email)
                page.click("button[type=submit]")
                page.wait_for_timeout(2000)
                # Vercel sends magic link — can't auto-complete without email access
                browser.close()
                return {
                    "token": None,
                    "created": False,
                    "needs_email_link": True,
                    "note": "Vercel sent a magic link to %s. Click it then reconnect." % email,
                }

            # Extract token from account settings
            page.goto("https://vercel.com/account/tokens", timeout=30000)
            page.wait_for_timeout(2000)

            # Click create token
            create_btn = page.locator("button:has-text('Create')")
            if create_btn.count() > 0:
                create_btn.click()
                page.wait_for_timeout(1000)
                page.fill("input[placeholder*='Token Name']", "Astra Deploy Token")
                page.click("button:has-text('Create Token')")
                page.wait_for_timeout(1000)
                token_el = page.locator("input[readonly]").first
                token = token_el.input_value() if token_el.count() > 0 else None
            else:
                token = None

            browser.close()
            return {
                "token": token,
                "created": token is not None,
                "note": "Vercel deploy token created." if token else "Token extraction failed — create at vercel.com/account/tokens",
            }

        except PWTimeout as e:
            try:
                browser.close()
            except Exception:
                pass
            return {"token": None, "created": False, "error": "Timeout"}
        except Exception as e:
            try:
                browser.close()
            except Exception:
                pass
            return {"token": None, "created": False, "error": str(e)}


def provision_sendgrid(email: str, password: str) -> dict:
    """
    Create SendGrid account and extract API key.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        try:
            page.goto("https://signup.sendgrid.com/", timeout=30000)
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)

            # Fill required fields
            username_field = page.locator("input[name='username']")
            if username_field.count() > 0:
                username_field.fill(_slug(email))

            page.click("button[type=submit]")
            page.wait_for_timeout(3000)

            if "app.sendgrid.com" not in page.url:
                # May need email verification
                browser.close()
                return {
                    "api_key": None,
                    "created": False,
                    "needs_verification": True,
                    "note": "SendGrid sent a verification email to %s. Verify then reconnect." % email,
                }

            # Create API key
            page.goto("https://app.sendgrid.com/settings/api_keys", timeout=30000)
            page.wait_for_timeout(2000)
            page.click("button:has-text('Create API Key')")
            page.wait_for_timeout(1000)
            page.fill("input[name='name']", "Astra Marketing Key")
            # Full access
            page.click("label:has-text('Full Access')")
            page.click("button:has-text('Create & View')")
            page.wait_for_timeout(2000)

            key_el = page.locator(".api-key-text, code, input[readonly]").first
            api_key = key_el.text_content() or key_el.input_value() if key_el.count() > 0 else None

            browser.close()
            return {
                "api_key": api_key,
                "created": api_key is not None,
                "note": "SendGrid key created." if api_key else "Key extraction failed — create at app.sendgrid.com/settings/api_keys",
            }

        except Exception as e:
            try:
                browser.close()
            except Exception:
                pass
            return {"api_key": None, "created": False, "error": str(e)}


def _slug(email: str) -> str:
    base = email.split("@")[0].lower().replace(".", "-").replace("_", "-")
    suffix = secrets.token_hex(3)
    return f"{base}-{suffix}"[:39]  # GitHub username max 39 chars
