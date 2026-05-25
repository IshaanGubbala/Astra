"""Microsoft Clarity tools — heatmaps + session recording integration code gen."""
import logging
logger = logging.getLogger(__name__)


def clarity_generate_integration(project_id: str = "", framework: str = "nextjs") -> dict:
    """
    Generate Microsoft Clarity integration for a user's app.
    project_id: from Clarity dashboard (or leave blank for template)
    framework: nextjs | react | html
    """
    pid = project_id or "YOUR_PROJECT_ID"

    if framework == "nextjs":
        return {
            "framework": "nextjs",
            "install": "npm install clarity-js",
            "script_tag": (
                f"// app/clarity.tsx — add to layout\n"
                f"'use client'\n"
                f"import {{ useEffect }} from 'react';\n\n"
                f"export function MicrosoftClarity() {{\n"
                f"  useEffect(() => {{\n"
                f"    if (typeof window !== 'undefined') {{\n"
                f"      (function(c,l,a,r,i,t,y){{\n"
                f"        c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};\n"
                f"        t=l.createElement(r);t.async=1;t.src='https://www.clarity.ms/tag/'+i;\n"
                f"        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);\n"
                f"      }})(window, document, 'clarity', 'script', '{pid}');\n"
                f"    }}\n"
                f"  }}, []);\n"
                f"  return null;\n"
                f"}}"
            ),
            "layout_usage": f"<MicrosoftClarity /> // add inside <body> in layout.tsx",
            "env_var": "NEXT_PUBLIC_CLARITY_PROJECT_ID",
            "dashboard": f"https://clarity.microsoft.com/projects/view/{pid}/dashboard",
            "features": ["Heatmaps", "Session recordings", "Rage clicks", "Dead clicks", "Scroll depth"],
            "setup_steps": [
                "1. Go to https://clarity.microsoft.com and create project",
                "2. Copy Project ID",
                "3. Add MicrosoftClarity component to layout.tsx",
                "4. Deploy and wait 24h for data",
            ],
        }
    elif framework == "html":
        return {
            "script": (
                f"<script type='text/javascript'>\n"
                f"  (function(c,l,a,r,i,t,y){{\n"
                f"    c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};\n"
                f"    t=l.createElement(r);t.async=1;t.src='https://www.clarity.ms/tag/'+i;\n"
                f"    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);\n"
                f"  }})(window, document, 'clarity', 'script', '{pid}');\n"
                f"</script>"
            ),
            "placement": "Paste before </head>",
        }
    return {"error": f"Unsupported framework: {framework}"}


def clarity_custom_tags(tags: dict) -> dict:
    """
    Generate Clarity custom tag code for segmenting sessions.
    tags: {'plan': 'pro', 'user_type': 'founder'}
    """
    lines = ["// Tag sessions for filtering in Clarity dashboard"]
    for key, value in tags.items():
        lines.append(f"window.clarity('set', '{key}', '{value}');")
    return {
        "code": "\n".join(lines),
        "usage": "Call after user signs in to segment recordings by plan, user type, etc.",
    }


def clarity_setup_for_app(app_name: str, app_type: str = "saas") -> dict:
    """Full Clarity setup package for a user's app — integration + custom tags."""
    return {
        "app": app_name,
        "integration": clarity_generate_integration(framework="nextjs"),
        "recommended_tags": clarity_custom_tags({
            "plan": "{{user.plan}}",
            "user_id": "{{user.id}}",
            "app_type": app_type,
        }),
        "pages_to_monitor": ["landing", "onboarding", "dashboard", "pricing", "settings"],
        "what_to_watch": [
            "Rage clicks on broken buttons",
            "Dead zones on landing page hero",
            "Drop-off point in onboarding flow",
            "Scroll depth on pricing page",
        ],
    }
