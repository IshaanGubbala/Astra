"""
Teardown script — deletes test accounts on GitHub, SendGrid, Vercel, Composio.
Run between test runs to get a clean slate.
"""
import logging
import time

logger = logging.getLogger(__name__)


def teardown_github(email: str, password: str) -> dict:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context().new_page()
        try:
            page.goto("https://github.com/login", timeout=30000)
            page.fill("input#login_field", email)
            page.fill("input#password", password)
            page.click("input[type=submit]")
            page.wait_for_timeout(3000)
            if "login" in page.url:
                browser.close()
                return {"deleted": False, "note": "Login failed — account may not exist"}

            page.goto("https://github.com/settings/profile", timeout=30000)
            page.wait_for_timeout(1000)
            # Navigate to delete account section
            page.goto("https://github.com/settings/admin", timeout=30000)
            page.wait_for_timeout(2000)

            delete_btn = page.locator("button:has-text('Delete your account'), summary:has-text('Delete this account')").first
            if delete_btn.count() > 0:
                delete_btn.click()
                page.wait_for_timeout(1000)
                # Confirm username
                username_input = page.locator("input[name='verify']").first
                if username_input.count() > 0:
                    username = page.locator("meta[name='user-login']").get_attribute("content") or ""
                    username_input.fill(username)
                confirm_btn = page.locator("button:has-text('Delete this account')").last
                if confirm_btn.count() > 0:
                    confirm_btn.click()
                    page.wait_for_timeout(3000)
                    browser.close()
                    return {"deleted": True}

            browser.close()
            return {"deleted": False, "note": "Delete button not found — delete manually at github.com/settings/admin"}
        except Exception as e:
            try: browser.close()
            except Exception: pass
            return {"deleted": False, "error": str(e)}


def teardown_sendgrid(email: str, password: str) -> dict:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context().new_page()
        try:
            page.goto("https://app.sendgrid.com/login", timeout=30000)
            page.fill("input[name='email'], input[type=email]", email)
            page.fill("input[name='password'], input[type=password]", password)
            page.click("button[type=submit]")
            page.wait_for_timeout(4000)
            if "app.sendgrid.com" not in page.url:
                browser.close()
                return {"deleted": False, "note": "Login failed"}

            page.goto("https://app.sendgrid.com/settings/account", timeout=30000)
            page.wait_for_timeout(2000)
            close_btn = page.locator("button:has-text('Close Account'), a:has-text('Close Account')").first
            if close_btn.count() > 0:
                close_btn.click()
                page.wait_for_timeout(2000)
                confirm = page.locator("button:has-text('Confirm')").first
                if confirm.count() > 0:
                    confirm.click()
                    page.wait_for_timeout(2000)
                    browser.close()
                    return {"deleted": True}

            browser.close()
            return {"deleted": False, "note": "Close Account button not found — delete at app.sendgrid.com/settings/account"}
        except Exception as e:
            try: browser.close()
            except Exception: pass
            return {"deleted": False, "error": str(e)}


def teardown_all(email: str, password: str) -> dict:
    results = {}
    logger.info("Tearing down GitHub…")
    results["github"] = teardown_github(email, password)
    logger.info("Tearing down SendGrid…")
    results["sendgrid"] = teardown_sendgrid(email, password)
    return results
