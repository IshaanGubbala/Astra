"""YouTube and TikTok competitor content analysis via yt-dlp + youtube-transcript-api."""
import json
import subprocess
import sys
import textwrap
from typing import Any


def _yt_dlp(*args: str) -> dict[str, Any] | list[Any] | None:
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--quiet", *args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return None
        return json.loads(result.stdout) if result.stdout.strip() else None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None


def _get_transcript(video_id: str) -> str:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])
        return " ".join(s["text"] for s in segments)[:4000]
    except Exception:
        return ""


def _format_duration(seconds: int | None) -> str:
    if not seconds:
        return "unknown"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h{m}m{s}s" if h else f"{m}m{s}s"


def youtube_research(query: str, max_results: int = 5) -> str:
    """Search YouTube for competitor/topic videos; return metadata + transcript summaries."""
    search_data = _yt_dlp(
        f"ytsearch{max_results}:{query}",
        "--dump-json",
        "--flat-playlist",
        "--no-playlist",
    )

    if not search_data:
        return f"[youtube_research] No results for: {query}"

    entries: list[dict] = []
    if isinstance(search_data, dict):
        entries = search_data.get("entries", [])
    elif isinstance(search_data, list):
        entries = search_data

    if not entries:
        # yt-dlp flat-playlist may output one JSON per line
        return f"[youtube_research] No entries parsed for: {query}"

    sections: list[str] = [f"## YouTube Research: {query}\n"]
    for entry in entries[:max_results]:
        vid_id = entry.get("id") or entry.get("display_id", "")
        title = entry.get("title", "untitled")
        channel = entry.get("uploader") or entry.get("channel", "unknown")
        views = entry.get("view_count")
        likes = entry.get("like_count")
        duration = _format_duration(entry.get("duration"))
        url = entry.get("webpage_url") or f"https://youtu.be/{vid_id}"
        description = (entry.get("description") or "")[:800]
        transcript = _get_transcript(vid_id) if vid_id else ""

        block = [
            f"### {title}",
            f"**Channel:** {channel} | **Views:** {views:,} | **Likes:** {likes} | **Duration:** {duration}" if views else f"**Channel:** {channel} | **Duration:** {duration}",
            f"**URL:** {url}",
        ]
        if description:
            block.append(f"**Description:** {description[:400]}")
        if transcript:
            block.append(f"**Transcript excerpt:**\n{textwrap.shorten(transcript, 1200, placeholder='...')}")
        sections.append("\n".join(block))

    return "\n\n".join(sections)


def tiktok_research(query: str, max_results: int = 5) -> str:
    """Search TikTok for competitor/topic videos; return metadata + captions."""
    search_data = _yt_dlp(
        f"tiktoksearch{max_results}:{query}",
        "--dump-json",
        "--flat-playlist",
        "--no-playlist",
    )

    if not search_data:
        # Fallback: hashtag search
        tag = query.replace(" ", "").lower()
        search_data = _yt_dlp(
            f"https://www.tiktok.com/tag/{tag}",
            "--dump-json",
            "--flat-playlist",
            "--playlist-items", f"1-{max_results}",
        )

    if not search_data:
        return f"[tiktok_research] No results for: {query}"

    entries: list[dict] = []
    if isinstance(search_data, dict):
        entries = search_data.get("entries", [search_data]) if "entries" in search_data else [search_data]
    elif isinstance(search_data, list):
        entries = search_data

    sections: list[str] = [f"## TikTok Research: {query}\n"]
    for entry in entries[:max_results]:
        title = entry.get("title") or entry.get("description", "untitled")
        creator = entry.get("uploader") or entry.get("creator") or entry.get("channel", "unknown")
        views = entry.get("view_count")
        likes = entry.get("like_count")
        url = entry.get("webpage_url") or entry.get("url", "")
        description = (entry.get("description") or "")[:600]
        # TikTok captions stored in subtitles/automatic_captions
        caption = ""
        subtitles = entry.get("subtitles") or entry.get("automatic_captions") or {}
        for lang_data in subtitles.values():
            if isinstance(lang_data, list) and lang_data:
                raw = lang_data[0].get("data", "") or ""
                caption = str(raw)[:1000]
                break

        block = [f"### {title[:120]}"]
        meta_parts = [f"**Creator:** {creator}"]
        if views:
            meta_parts.append(f"**Views:** {views:,}")
        if likes:
            meta_parts.append(f"**Likes:** {likes:,}")
        if url:
            meta_parts.append(f"**URL:** {url}")
        block.append(" | ".join(meta_parts))
        if description and description != title:
            block.append(f"**Caption:** {description[:400]}")
        if caption:
            block.append(f"**Subtitles excerpt:** {textwrap.shorten(caption, 600, placeholder='...')}")
        sections.append("\n".join(block))

    return "\n\n".join(sections)
