"""Obsidian vault tools for agents — read past context, write structured session notes."""
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.config import settings


def _vault(founder_id: str | None = None) -> Path:
    base = Path(settings.obsidian_vault).expanduser()
    if founder_id:
        return base / "founders" / founder_id
    return base


def obsidian_read(agent: str, max_notes: int = 5, founder_id: str | None = None) -> dict:
    """
    Read recent session notes from the agent's vault folder.
    Returns accumulated knowledge the agent can use as context.
    """
    folder = _vault(founder_id) / agent
    if not folder.exists():
        return {"notes": [], "summary": "No prior notes found."}

    notes = sorted(folder.glob("*.md"), reverse=True)
    notes = [n for n in notes if n.stem != "README"][:max_notes]

    results = []
    for note in notes:
        try:
            text = note.read_text()
            results.append({"file": note.name, "content": text[:2000]})
        except Exception:
            pass

    return {
        "notes": results,
        "count": len(results),
        "summary": f"{len(results)} prior session(s) found." if results else "No prior sessions.",
    }


def format_vault_context(agent: str, max_notes: int = 3, founder_id: str | None = None) -> str:
    """
    Return vault notes as a human-readable markdown block for injection into agent prompts.
    Much more useful to the LLM than a raw JSON dict.
    """
    ctx = obsidian_read(agent, max_notes=max_notes, founder_id=founder_id)
    notes = ctx.get("notes", [])
    if not notes:
        return ""

    lines = [f"## Your Prior Session Notes ({len(notes)} most recent)\n"]
    for note in notes:
        lines.append(f"### {note['file']}")
        lines.append(note["content"].strip())
        lines.append("")
    return "\n".join(lines)


def obsidian_log(
    agent: str,
    session_id: str,
    summary: str,
    output: dict = None,
    tags: list[str] = None,
    links: list[str] = None,
    founder_id: str | None = None,
) -> dict:
    """
    Write a structured session note to the agent's vault folder.
    - summary: what the agent did this session (prose)
    - output: key results as a dict (files created, URLs, decisions)
    - tags: obsidian tags e.g. ["nda", "acmeco"]
    - links: wikilinks to other agent notes e.g. ["[[research/2026-05-24-abc]]"]
    - founder_id: namespaces vault per founder (optional)
    """
    folder = _vault(founder_id) / agent
    folder.mkdir(parents=True, exist_ok=True)

    date = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")
    filename = folder / f"{date}-{session_id[:8]}.md"

    tag_str = " ".join(f"#{t}" for t in (tags or [])) or ""
    link_str = "\n".join(f"- {lnk}" for lnk in (links or []))

    sections = [
        f"---",
        f"date: {date}",
        f"session: {session_id}",
        f"agent: {agent}",
        f"founder_id: {founder_id or 'default'}",
        f"tags: [{', '.join(tags or [])}]",
        f"---",
        f"",
        f"# {agent.capitalize()} · {date} {time_str}",
        f"",
    ]

    if tag_str:
        sections += [tag_str, ""]

    sections += ["## Summary", summary, ""]

    if output:
        sections += ["## Outputs"]
        for key, val in output.items():
            if isinstance(val, (dict, list)):
                sections.append(f"**{key}:**")
                sections.append(f"```json\n{json.dumps(val, indent=2)[:1500]}\n```")
            else:
                sections.append(f"**{key}:** {val}")
        sections.append("")

    if links:
        sections += ["## Related", link_str, ""]

    filename.write_text("\n".join(sections))
    return {"logged": True, "path": str(filename), "note": filename.name}


def obsidian_append(
    agent: str,
    session_id: str,
    heading: str,
    content: str,
    founder_id: str | None = None,
) -> dict:
    """Append a new section to an existing session note mid-run."""
    folder = _vault(founder_id) / agent
    date = datetime.now().strftime("%Y-%m-%d")
    filename = folder / f"{date}-{session_id[:8]}.md"

    if not filename.exists():
        folder.mkdir(parents=True, exist_ok=True)
        time_str = datetime.now().strftime("%H:%M")
        filename.write_text(
            f"---\ndate: {date}\nsession: {session_id}\nagent: {agent}\nfounder_id: {founder_id or 'default'}\n---\n\n"
            f"# {agent.capitalize()} · {date} {time_str}\n\n## Summary\n(auto-created)\n"
        )

    existing = filename.read_text()
    addition = f"\n## {heading}\n{content}\n"
    filename.write_text(existing + addition)
    return {"appended": True, "heading": heading}


def auto_log_if_missing(
    agent: str,
    session_id: str,
    result: dict,
    founder_id: str | None = None,
) -> bool:
    """
    Called after every agent run. Writes a vault note only if the agent
    didn't call obsidian_log itself during the run.
    Returns True if a note was auto-written.
    """
    folder = _vault(founder_id) / agent
    date = datetime.now().strftime("%Y-%m-%d")
    expected_note = folder / f"{date}-{session_id[:8]}.md"

    if expected_note.exists():
        return False  # agent already wrote its own note

    # Auto-generate a minimal note from the agent's output
    summary = result.get("summary") or result.get("output_summary") or "Agent completed task."
    if not isinstance(summary, str):
        summary = "Agent completed task."

    # Extract key outputs from result dict
    output_keys = {k: v for k, v in result.items() if k not in ("mirror_verdict", "mirror_critique") and v}

    obsidian_log(
        agent=agent,
        session_id=session_id,
        summary=f"[Auto-logged] {summary}",
        output=output_keys if output_keys else None,
        tags=["auto-logged"],
        founder_id=founder_id,
    )
    return True


def obsidian_session_index(
    session_id: str,
    goal: str,
    agents_completed: list[str],
    founder_id: str | None = None,
) -> dict:
    """
    Write a session-level index note that links all agent notes for this run.
    Stored at vault_root/sessions/<date>-<session_id>.md
    """
    folder = _vault(founder_id) / "sessions"
    folder.mkdir(parents=True, exist_ok=True)

    date = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")
    filename = folder / f"{date}-{session_id[:8]}.md"

    agent_links = []
    for agent in agents_completed:
        note_path = f"[[{agent}/{date}-{session_id[:8]}]]"
        agent_links.append(f"- {note_path}")

    sections = [
        f"---",
        f"date: {date}",
        f"session: {session_id}",
        f"type: session-index",
        f"founder_id: {founder_id or 'default'}",
        f"agents: [{', '.join(agents_completed)}]",
        f"---",
        f"",
        f"# Session {session_id[:8]} · {date} {time_str}",
        f"",
        f"**Goal:** {goal}",
        f"",
        f"## Agents That Ran",
        *agent_links,
        f"",
        f"## Cross-Agent Links",
    ]

    # Add wikilinks between related agent pairs
    pairs = [
        ("research", "web", "Research findings fed into landing page"),
        ("research", "legal", "Market context informed legal structure"),
        ("research", "marketing", "Market data used for campaign targeting"),
        ("research", "ops", "Market analysis included in exec summary"),
        ("web", "technical", "Landing page repo linked to scaffold"),
    ]
    for a, b, note in pairs:
        if a in agents_completed and b in agents_completed:
            sections.append(f"- [[{a}/{date}-{session_id[:8]}]] → [[{b}/{date}-{session_id[:8]}]]: {note}")

    sections.append("")
    filename.write_text("\n".join(sections))
    return {"indexed": True, "path": str(filename), "note": filename.name}
