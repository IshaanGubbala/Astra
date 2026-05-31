"""
claude_code_scaffold — delegates to run_mvp_loop for reliable per-file scaffolding.
The technical agent calls this after github_create_repo to get actual working code into the repo.
"""
import logging
import uuid

logger = logging.getLogger(__name__)


def claude_code_scaffold(
    repo_url: str,
    task: str = "",
    goal: str = "",
    commit_message: str = "feat: scaffold via claude code",
    context: str = "",
    api_key: str = "",
    **_kwargs,
) -> dict:
    """
    Clone a GitHub repo, run Claude Code to implement the task, commit and push.

    Delegates to run_mvp_loop which writes one file at a time with verification,
    avoiding the single-shot prompt approach that frequently produces no files.

    Args:
        repo_url: full GitHub HTTPS URL (e.g. https://github.com/org/repo)
        task: detailed instruction for Claude Code (what to build / scaffold). Also accepts 'goal' as alias.
        goal: alias for task (accepted for agent compatibility)
        context: optional extra context (research findings, session notes, etc.)
    Returns: {success, repo_url, files_scaffolded, commit, error?}
    """
    from backend.tools.git_tools import run_mvp_loop

    task = task or goal
    session_id = str(uuid.uuid4())

    try:
        result = run_mvp_loop(
            repo_url=repo_url,
            goal=task,
            session_id=session_id,
            context=context,
        )
        # Normalize return shape to match what the agent expects
        files = result.get("files_preview", [])
        file_count = result.get("files_in_repo", len(files))
        commits = result.get("commits", [])
        return {
            "success": not result.get("error"),
            "repo_url": repo_url,
            "files_scaffolded": file_count,
            "files_in_repo": file_count,
            "commit": commits[-1] if commits else None,
            "output_preview": f"Scaffolded {file_count} files: {', '.join(files[:8])}",
            **({"error": result["error"]} if result.get("error") else {}),
        }
    except Exception as e:
        logger.error("claude_code_scaffold failed: %s", e)
        return {"error": str(e), "success": False}
