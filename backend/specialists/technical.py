"""Technical specialist — GitHub repos, issues, PRs, Linear, Notion."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.github_scaffold import github_create_repo
from backend.tools.claude_scaffold import claude_code_scaffold
from backend.tools.composio_tools import (
    composio_linear_create_issue,
    composio_notion_create_page,
)


def build_technical_agent(**kwargs) -> Agent:
    return Agent(
        name="technical",
        role=(
            "You are the technical specialist. Your agent name is 'technical'. "
            "Start every session by calling obsidian_read(agent='technical') to load prior context. "
            "WORKFLOW — follow in order: "
            "(1) Call github_create_repo to create the repo and get repo_url. "
            "(2) Call claude_code_scaffold(repo_url=<from step 1>, "
            "task=<full description: product name, what it does, stack, key entities/endpoints>, "
            "context=<paste the vault_context and prior_results from SHARED CONTEXT — this gives Claude Code "
            "the research findings, market data, and other agent outputs to build the right product>). "
            "This runs real Claude Code in the repo and pushes actual working code — it is the main deliverable. "
            "(3) Call composio_linear_create_issue for 2-3 key MVP tickets. "
            "(4) Call obsidian_log(agent='technical', session_id=<from context>, summary=..., output=...) then done."
        ),
        tools={
            "github_create_repo": github_create_repo,
            "claude_code_scaffold": claude_code_scaffold,
            "composio_linear_create_issue": composio_linear_create_issue,
            "composio_notion_create_page": composio_notion_create_page,
                    "obsidian_log": obsidian_log,
            "obsidian_read": obsidian_read,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
