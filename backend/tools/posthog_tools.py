"""PostHog analytics tools — setup, event tracking code gen, funnel analysis."""
import logging
import requests
from backend.config import settings

logger = logging.getLogger(__name__)
_API = "https://app.posthog.com/api"


def _headers():
    key = getattr(settings, "posthog_api_key", "")
    return {"Authorization": f"Bearer {key}"} if key else {}


def posthog_generate_integration(app_name: str, framework: str = "nextjs") -> dict:
    """
    Generate PostHog analytics integration for a user's app.
    framework: nextjs | react | node | python
    """
    if framework == "nextjs":
        return {
            "app": app_name,
            "install": "npm install posthog-js posthog-node",
            "env_vars": {
                "NEXT_PUBLIC_POSTHOG_KEY": "phc_your_key_here",
                "NEXT_PUBLIC_POSTHOG_HOST": "https://app.posthog.com",
            },
            "provider": (
                "// app/providers.tsx\n"
                "'use client'\n"
                "import posthog from 'posthog-js';\n"
                "import { PostHogProvider } from 'posthog-js/react';\n"
                "import { useEffect } from 'react';\n\n"
                "export function PHProvider({ children }: { children: React.ReactNode }) {\n"
                "  useEffect(() => {\n"
                "    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {\n"
                "      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,\n"
                "      capture_pageview: false,\n"
                "    });\n"
                "  }, []);\n"
                "  return <PostHogProvider client={posthog}>{children}</PostHogProvider>;\n"
                "}"
            ),
            "pageview": (
                "// app/posthog-pageview.tsx\n"
                "'use client'\n"
                "import { usePathname, useSearchParams } from 'next/navigation';\n"
                "import { usePostHog } from 'posthog-js/react';\n"
                "import { useEffect } from 'react';\n\n"
                "export function PostHogPageview() {\n"
                "  const pathname = usePathname();\n"
                "  const posthog = usePostHog();\n"
                "  useEffect(() => { posthog.capture('$pageview'); }, [pathname]);\n"
                "  return null;\n"
                "}"
            ),
            "events": (
                "// Track key events\n"
                "import { usePostHog } from 'posthog-js/react';\n"
                "const posthog = usePostHog();\n\n"
                "posthog.capture('user_signed_up', { plan: 'free' });\n"
                "posthog.capture('goal_submitted', { goal_length: goal.length });\n"
                "posthog.capture('upgrade_clicked', { from_page: 'dashboard' });"
            ),
            "key_events": [
                "user_signed_up", "user_logged_in", "goal_submitted",
                "agent_run_started", "agent_run_completed", "upgrade_clicked",
                "feature_used",
            ],
        }
    elif framework == "python":
        return {
            "install": "pip install posthog",
            "setup": (
                "from posthog import Posthog\n"
                "posthog = Posthog(project_api_key='phc_...', host='https://app.posthog.com')\n\n"
                "posthog.capture('user_id', 'event_name', {'property': 'value'})"
            ),
        }
    return {"error": f"Unsupported framework: {framework}"}


def posthog_create_key_events_spec(app_name: str, app_type: str = "saas") -> dict:
    """
    Generate a PostHog event tracking specification for a SaaS app.
    Returns the key events to track with properties.
    """
    events = {
        "saas": [
            {"event": "user_signed_up", "properties": ["plan", "source", "referrer"]},
            {"event": "onboarding_completed", "properties": ["steps_completed", "time_to_complete"]},
            {"event": "feature_used", "properties": ["feature_name", "session_id"]},
            {"event": "upgrade_viewed", "properties": ["current_plan", "from_page"]},
            {"event": "upgrade_completed", "properties": ["from_plan", "to_plan", "mrr"]},
            {"event": "session_started", "properties": ["agent_count"]},
            {"event": "agent_completed", "properties": ["agent_name", "duration_ms", "verdict"]},
            {"event": "churn_risk", "properties": ["days_inactive", "last_feature_used"]},
        ],
        "marketplace": [
            {"event": "listing_viewed", "properties": ["listing_id", "category"]},
            {"event": "purchase_started", "properties": ["item_id", "price"]},
            {"event": "purchase_completed", "properties": ["item_id", "price", "payment_method"]},
        ],
    }
    return {
        "app": app_name,
        "events": events.get(app_type, events["saas"]),
        "funnels": [
            {"name": "Activation", "steps": ["user_signed_up", "onboarding_completed", "feature_used"]},
            {"name": "Conversion", "steps": ["upgrade_viewed", "upgrade_completed"]},
        ],
        "dashboard_url": "https://app.posthog.com",
    }


def posthog_get_insights(event_name: str, days: int = 30) -> dict:
    """Fetch event count from PostHog API for a given event."""
    if not _headers():
        return {"note": "POSTHOG_API_KEY not set", "event": event_name}
    try:
        project_id = getattr(settings, "posthog_project_id", "")
        resp = requests.get(
            f"{_API}/projects/{project_id}/events/",
            headers=_headers(),
            params={"event": event_name, "limit": 100},
            timeout=10,
        )
        data = resp.json()
        return {"event": event_name, "count": len(data.get("results", [])), "days": days}
    except Exception as e:
        return {"error": str(e)}
