"""
Git tools for the technical agent — write files, commit, push to a GitHub repo.
run_mvp_loop is the primary entry point: iterates Claude Code until MVP is complete.
"""
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)

CLAUDE_BIN = "/Users/ishaangubbala/.local/bin/claude"

# session_id -> cloned tmpdir path (kept alive for iterative commits)
_clones: dict[str, str] = {}


def _clone_url(repo_url: str) -> str:
    token = settings.github_token
    if token and "github.com" in repo_url:
        return repo_url.replace("https://", f"https://{token}@")
    return repo_url


def _sh(cmd: list, cwd: str = None, timeout: int = 60) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:2])} failed: {r.stderr[:300]}")
    return r.stdout.strip()


def _ensure_clone(repo_url: str, session_id: str = "default") -> str:
    """Clone repo once per session, return local path."""
    key = f"{session_id}:{repo_url}"
    if key in _clones and os.path.isdir(_clones[key]):
        return _clones[key]
    tmpdir = tempfile.mkdtemp(prefix="astra_repo_")
    _sh(["git", "clone", "--depth", "1", _clone_url(repo_url), tmpdir])
    _sh(["git", "config", "user.email", "astra-agent@astra.ai"], cwd=tmpdir)
    _sh(["git", "config", "user.name", "Astra Agent"], cwd=tmpdir)
    _clones[key] = tmpdir
    return tmpdir


def _pull(local: str) -> None:
    try:
        _sh(["git", "pull", "--rebase"], cwd=local, timeout=30)
    except Exception:
        pass


def _staged_files(local: str) -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached"], cwd=local, capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if l.strip()]


def _commit_and_push(local: str, message: str) -> str | None:
    """Stage all, commit if dirty, push. Returns short SHA or None."""
    status = subprocess.run(["git", "status", "--porcelain"], cwd=local, capture_output=True, text=True).stdout.strip()
    if status:
        _sh(["git", "add", "-A"], cwd=local)
        _sh(["git", "commit", "-m", message], cwd=local)
    try:
        ahead = _sh(["git", "rev-list", "--count", "HEAD@{upstream}..HEAD"], cwd=local)
    except Exception:
        ahead = "1"
    if ahead == "0":
        return None
    push = subprocess.run(["git", "push"], cwd=local, capture_output=True, text=True, timeout=60)
    if push.returncode != 0:
        raise RuntimeError(f"git push failed: {push.stderr[:200]}")
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=local, capture_output=True, text=True).stdout.strip()


def _run_claude(local: str, prompt: str, timeout: int = 360) -> str:
    """Run Claude Code non-interactively with --print, return stdout."""
    if not os.path.exists(CLAUDE_BIN):
        raise RuntimeError(f"Claude Code not found at {CLAUDE_BIN}")
    env = os.environ.copy()
    r = subprocess.run(
        [CLAUDE_BIN, "--print", prompt, "--output-format", "text", "--dangerously-skip-permissions"],
        cwd=local,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    if r.returncode not in (0, 1):
        logger.warning("claude exited %d: %s", r.returncode, r.stderr[:200])
    return r.stdout.strip()


def run_mvp_loop(
    repo_url: str,
    goal: str,
    session_id: str = "default",
    context: str = "",
    required_files: list[str] = None,
    max_rounds: int = 6,
) -> dict:
    """
    Iteratively run Claude Code inside a GitHub repo until an MVP is complete.
    Each round: check what exists, give Claude targeted instructions, commit+push.
    Loops until required_files all exist or max_rounds reached.

    Args:
        repo_url: GitHub HTTPS URL
        goal: what product to build (e.g. "hormone tracking SaaS")
        session_id: shared clone key — pass same value across all calls for this session
        context: extra context (research notes, prior agent outputs)
        required_files: list of paths that must exist for MVP to be considered done.
                        Defaults to a standard Next.js+FastAPI set.
        max_rounds: max Claude Code iterations (default 6)
    Returns: {success, repo_url, commits, files_in_repo, rounds_run}
    """
    if not settings.github_token:
        return {"error": "GITHUB_TOKEN not set"}

    if required_files is None:
        required_files = [
            "frontend/package.json",
            "frontend/app/page.tsx",
            "backend/main.py",
            "README.md",
        ]

    ctx_block = f"\n\nCONTEXT FROM RESEARCH + OTHER AGENTS:\n{context}\n" if context else ""

    ROUND_PROMPTS = [
        # Round 1 — full frontend scaffold
        f"""You are building a production MVP for: {goal}{ctx_block}

INSTRUCTIONS — follow exactly:
1. Use the Write tool to create EVERY file listed below immediately. No planning, no explanation — just write the files.
2. After writing all files, run: bash -c "git add -A && git commit -m 'feat: frontend scaffold'"

CREATE THESE FILES with real working code (no TODOs, no placeholders):
- frontend/package.json  (Next.js 14, TypeScript, Tailwind, shadcn/ui)
- frontend/tailwind.config.ts
- frontend/tsconfig.json
- frontend/next.config.js
- frontend/app/layout.tsx  (root layout with Tailwind + fonts)
- frontend/app/page.tsx  (compelling landing/home page specific to {goal})
- frontend/app/dashboard/page.tsx  (main dashboard for logged-in users)
- frontend/app/dashboard/layout.tsx
- frontend/components/Navbar.tsx
- frontend/components/Hero.tsx  (landing hero section)
- frontend/components/Features.tsx  (feature highlights)

Make all UI specific to {goal}. Use real feature names, real value props, real copy.""",

        # Round 2 — backend + API
        f"""Continue building the MVP for: {goal}

The frontend was scaffolded. Now build the backend.
Run: bash -c "git add -A && git commit -m 'feat: backend API'" after writing all files.

CREATE THESE FILES:
- backend/main.py  (FastAPI app with CORS, all routers mounted)
- backend/models.py  (Pydantic + SQLAlchemy models specific to {goal})
- backend/database.py  (SQLAlchemy async engine + session)
- backend/routers/__init__.py
- backend/routers/auth.py  (POST /register, POST /login, GET /me — JWT auth)
- backend/routers/api.py  (core CRUD endpoints specific to {goal})
- backend/services/core.py  (business logic)
- backend/requirements.txt  (fastapi, uvicorn, sqlalchemy, pydantic, python-jose, passlib)
- .env.example  (all env vars the app needs)

All endpoints must be fully implemented — no raise NotImplementedError.""",

        # Round 3 — auth integration + DB
        f"""Continue the MVP for: {goal}

Add Clerk auth to frontend, Supabase client config, and wire them together.
Run: bash -c "git add -A && git commit -m 'feat: auth + db integration'" after writing all files.

CREATE/UPDATE:
- frontend/lib/supabase.ts  (Supabase client)
- frontend/lib/auth.ts  (Clerk + Supabase token exchange helper)
- frontend/middleware.ts  (Clerk auth middleware protecting /dashboard/*)
- frontend/app/sign-in/[[...sign-in]]/page.tsx  (Clerk SignIn component)
- frontend/app/sign-up/[[...sign-up]]/page.tsx  (Clerk SignUp component)
- frontend/app/dashboard/page.tsx  (UPDATE: add real data fetching from Supabase)
- docker-compose.yml  (postgres + backend + frontend services)
- frontend/.env.local.example""",

        # Round 4 — polish, error fixes, README
        f"""Final polish pass for the MVP: {goal}

Check existing files for issues and fix them. Add missing pieces.
Run: bash -c "git add -A && git commit -m 'feat: polish + README'" after changes.

DO:
1. Read frontend/app/page.tsx and frontend/app/dashboard/page.tsx — ensure they have real, specific content for {goal}
2. Create README.md with: project description, setup steps, env vars, how to run locally, tech stack
3. Create frontend/app/globals.css with Tailwind directives
4. Fix any obvious TypeScript errors in existing files
5. Ensure all imports in frontend files resolve (add missing component files if needed)
6. Add frontend/components/ui/ base components (Button, Card, Input) if not present""",

        # Round 5 — verification pass
        f"""Verification pass for: {goal}

Run: bash -c "ls -la frontend/app/ && ls -la backend/ && cat frontend/package.json" to check current state.
Then fix any critical gaps:
- If frontend/app/page.tsx has less than 50 lines, rewrite it with full landing page content
- If backend/main.py has less than 30 lines, complete it with all routers
- Ensure docker-compose.yml exists
- Run: bash -c "git add -A && git commit -m 'fix: verification pass'" if any changes made""",

        # Round 6 — final check
        f"""Final commit for: {goal}

Run: bash -c "git ls-files | head -40" to see all tracked files.
Add any missing files. Ensure the repo is a complete, working MVP.
Run: bash -c "git add -A && git commit -m 'feat: complete MVP'" if changes exist.""",
    ]

    try:
        local = _ensure_clone(repo_url, session_id)
        commits = []
        rounds_run = 0

        for i, prompt in enumerate(ROUND_PROMPTS[:max_rounds]):
            rounds_run += 1
            logger.info("MVP loop round %d/%d for %s", i + 1, max_rounds, repo_url)

            _pull(local)

            # Check if required files already exist — stop early if done
            existing = _staged_files(local)
            missing = [f for f in required_files if f not in existing]
            if not missing and i >= 2:
                logger.info("All required files present after round %d — done", i)
                break

            output = _run_claude(local, prompt, timeout=360)

            sha = _commit_and_push(local, f"feat: mvp round {i + 1} — {goal[:40]}")
            if sha:
                commits.append(sha)
                logger.info("Round %d committed: %s", i + 1, sha)

        # Final file count
        all_files = _staged_files(local)
        return {
            "success": True,
            "repo_url": repo_url,
            "github_url": f"{repo_url}/tree/main",
            "commits": commits,
            "rounds_run": rounds_run,
            "files_in_repo": len(all_files),
            "files_preview": all_files[:20],
        }

    except subprocess.TimeoutExpired:
        return {"error": "Timed out during MVP build"}
    except Exception as e:
        logger.error("run_mvp_loop failed: %s", e)
        return {"error": str(e)}


def run_claude_in_repo(
    repo_url: str,
    task: str,
    session_id: str = "default",
    context: str = "",
) -> dict:
    """
    Single Claude Code pass inside a repo. Commits + pushes whatever it writes.
    For full MVP building, prefer run_mvp_loop instead.
    """
    if not settings.github_token:
        return {"error": "GITHUB_TOKEN not set"}

    ctx_section = f"\n\nCONTEXT:\n{context}\n" if context else ""
    prompt = (
        f"Write REAL working code files immediately using the Write tool. No planning.\n\n"
        f"TASK: {task}{ctx_section}\n\n"
        f"After writing files, run: bash -c \"git add -A && git commit -m 'feat: {task[:60]}'\""
    )

    try:
        local = _ensure_clone(repo_url, session_id)
        _pull(local)
        _run_claude(local, prompt, timeout=360)
        sha = _commit_and_push(local, f"feat: {task[:72]}")
        files = _staged_files(local)
        return {
            "success": True,
            "repo_url": repo_url,
            "commit": sha,
            "files_in_repo": len(files),
            "github_url": f"{repo_url}/tree/main",
        }
    except subprocess.TimeoutExpired:
        return {"error": "Timed out (360s)"}
    except Exception as e:
        logger.error("run_claude_in_repo failed: %s", e)
        return {"error": str(e)}


def write_files_to_repo(
    repo_url: str,
    files: dict,
    commit_message: str = "feat: add files",
    session_id: str = "default",
) -> dict:
    """
    Write specific files directly to a GitHub repo and push.
    files: {"relative/path.ext": "file content string"}
    """
    if not settings.github_token:
        return {"error": "GITHUB_TOKEN not set"}
    if not files:
        return {"error": "No files provided"}
    try:
        local = _ensure_clone(repo_url, session_id)
        _pull(local)

        written = []
        for rel_path, content in files.items():
            full = Path(local) / rel_path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content if isinstance(content, str) else str(content), encoding="utf-8")
            written.append(rel_path)

        sha = _commit_and_push(local, commit_message)
        return {
            "success": True,
            "repo_url": repo_url,
            "commit": sha,
            "files_written": written,
            "github_url": f"{repo_url}/tree/main",
        }
    except Exception as e:
        logger.error("write_files_to_repo failed: %s", e)
        return {"error": str(e)}
