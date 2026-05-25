"""Clerk auth tools — generate Clerk integration code for user projects."""
import logging
logger = logging.getLogger(__name__)


def clerk_generate_integration(
    app_name: str,
    framework: str = "nextjs",
    features: list[str] = None,
) -> dict:
    """
    Generate complete Clerk auth integration for a user's app.
    framework: nextjs | react | node
    features: ['sign_in', 'sign_up', 'user_profile', 'organizations', 'webhooks']
    """
    features = features or ["sign_in", "sign_up", "user_profile"]

    if framework == "nextjs":
        return _nextjs_integration(app_name, features)
    elif framework == "react":
        return _react_integration(app_name, features)
    else:
        return _node_integration(app_name, features)


def _nextjs_integration(app_name: str, features: list[str]) -> dict:
    return {
        "app": app_name,
        "framework": "nextjs",
        "install": "npm install @clerk/nextjs",
        "env_vars": {
            "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY": "pk_test_...",
            "CLERK_SECRET_KEY": "sk_test_...",
            "NEXT_PUBLIC_CLERK_SIGN_IN_URL": "/sign-in",
            "NEXT_PUBLIC_CLERK_SIGN_UP_URL": "/sign-up",
            "NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL": "/dashboard",
            "NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL": "/onboarding",
        },
        "middleware": (
            "// middleware.ts\n"
            "import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';\n\n"
            "const isPublicRoute = createRouteMatcher(['/sign-in(.*)', '/sign-up(.*)', '/']);\n\n"
            "export default clerkMiddleware((auth, request) => {\n"
            "  if (!isPublicRoute(request)) auth().protect();\n"
            "});\n\n"
            "export const config = { matcher: ['/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)','/(api|trpc)(.*)'] };"
        ),
        "layout_wrapper": (
            "// app/layout.tsx — wrap with ClerkProvider\n"
            "import { ClerkProvider } from '@clerk/nextjs';\n\n"
            "export default function RootLayout({ children }) {\n"
            "  return (\n"
            "    <ClerkProvider>\n"
            "      <html lang='en'><body>{children}</body></html>\n"
            "    </ClerkProvider>\n"
            "  );\n"
            "}"
        ),
        "components": {
            "sign_in_page": (
                "// app/sign-in/[[...sign-in]]/page.tsx\n"
                "import { SignIn } from '@clerk/nextjs';\n"
                "export default function Page() { return <SignIn />; }"
            ),
            "sign_up_page": (
                "// app/sign-up/[[...sign-up]]/page.tsx\n"
                "import { SignUp } from '@clerk/nextjs';\n"
                "export default function Page() { return <SignUp />; }"
            ),
            "user_button": (
                "import { UserButton } from '@clerk/nextjs';\n"
                "<UserButton afterSignOutUrl='/' />"
            ),
            "get_user_server": (
                "import { auth, currentUser } from '@clerk/nextjs/server';\n\n"
                "export default async function Page() {\n"
                "  const { userId } = auth();\n"
                "  const user = await currentUser();\n"
                "  return <div>Hello {user?.firstName}</div>;\n"
                "}"
            ),
        },
        "dashboard_url": "https://dashboard.clerk.com",
        "features": features,
    }


def _react_integration(app_name: str, features: list[str]) -> dict:
    return {
        "app": app_name,
        "framework": "react",
        "install": "npm install @clerk/clerk-react",
        "env_vars": {"VITE_CLERK_PUBLISHABLE_KEY": "pk_test_..."},
        "setup": (
            "import { ClerkProvider, SignIn, SignUp, UserButton, useUser } from '@clerk/clerk-react';\n\n"
            "function App() {\n"
            "  return (\n"
            "    <ClerkProvider publishableKey={import.meta.env.VITE_CLERK_PUBLISHABLE_KEY}>\n"
            "      <YourApp />\n"
            "    </ClerkProvider>\n"
            "  );\n"
            "}"
        ),
    }


def _node_integration(app_name: str, features: list[str]) -> dict:
    return {
        "app": app_name,
        "framework": "node",
        "install": "npm install @clerk/clerk-sdk-node",
        "env_vars": {"CLERK_SECRET_KEY": "sk_test_..."},
        "middleware": (
            "import { ClerkExpressRequireAuth } from '@clerk/clerk-sdk-node';\n\n"
            "app.use('/api/protected', ClerkExpressRequireAuth(), (req, res) => {\n"
            "  const { userId } = req.auth;\n"
            "  res.json({ userId });\n"
            "});"
        ),
    }


def clerk_generate_webhook_handler(secret: str = "whsec_...") -> dict:
    """Generate Clerk webhook handler for syncing users to your database."""
    return {
        "install": "npm install svix",
        "handler": (
            "// app/api/webhooks/clerk/route.ts\n"
            "import { Webhook } from 'svix';\n"
            "import { headers } from 'next/headers';\n\n"
            "export async function POST(req: Request) {\n"
            "  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;\n"
            "  const wh = new Webhook(WEBHOOK_SECRET);\n"
            "  const body = await req.text();\n"
            "  const hdrs = headers();\n"
            "  const evt = wh.verify(body, {\n"
            "    'svix-id': hdrs.get('svix-id') ?? '',\n"
            "    'svix-timestamp': hdrs.get('svix-timestamp') ?? '',\n"
            "    'svix-signature': hdrs.get('svix-signature') ?? '',\n"
            "  });\n"
            "  if (evt.type === 'user.created') {\n"
            "    // sync to your DB: await db.users.create({ clerkId: evt.data.id })\n"
            "  }\n"
            "  return new Response('ok');\n"
            "}"
        ),
        "env_var": "CLERK_WEBHOOK_SECRET",
        "dashboard_url": "https://dashboard.clerk.com/webhooks",
    }
