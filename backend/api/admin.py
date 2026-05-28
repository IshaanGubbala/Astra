"""Admin monitoring endpoints — /admin/*"""
import asyncio
import os
import platform
import resource
import subprocess
import time
from datetime import datetime, timezone

import psutil
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.core.events import _sessions, _completed, _event_log, _event_counters, _steer

router = APIRouter(prefix="/admin")

_START_TIME = time.time()


def _uptime() -> str:
    secs = int(time.time() - _START_TIME)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


@router.get("/health")
async def health():
    return {"status": "ok", "uptime": _uptime(), "ts": datetime.now(timezone.utc).isoformat()}


@router.get("/system")
async def system_info():
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    boot = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).isoformat()

    proc = psutil.Process()
    with proc.oneshot():
        proc_mem = proc.memory_info()
        proc_cpu = proc.cpu_percent(interval=0.2)
        proc_threads = proc.num_threads()
        proc_fds = proc.num_fds() if hasattr(proc, "num_fds") else None
        proc_conns = len(proc.net_connections())

    return {
        "host": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "uptime": _uptime(),
        "boot_time": boot,
        "cpu": {
            "percent": cpu,
            "count_logical": psutil.cpu_count(logical=True),
            "count_physical": psutil.cpu_count(logical=False),
            "freq_mhz": round(psutil.cpu_freq().current, 1) if psutil.cpu_freq() else None,
            "load_avg_1m": round(os.getloadavg()[0], 2),
            "load_avg_5m": round(os.getloadavg()[1], 2),
            "load_avg_15m": round(os.getloadavg()[2], 2),
        },
        "memory": {
            "total_gb": round(mem.total / 1e9, 2),
            "used_gb": round(mem.used / 1e9, 2),
            "available_gb": round(mem.available / 1e9, 2),
            "percent": mem.percent,
            "swap_total_gb": round(psutil.swap_memory().total / 1e9, 2),
            "swap_used_gb": round(psutil.swap_memory().used / 1e9, 2),
        },
        "disk": {
            "total_gb": round(disk.total / 1e9, 2),
            "used_gb": round(disk.used / 1e9, 2),
            "free_gb": round(disk.free / 1e9, 2),
            "percent": disk.percent,
        },
        "network": {
            "bytes_sent_mb": round(net.bytes_sent / 1e6, 2),
            "bytes_recv_mb": round(net.bytes_recv / 1e6, 2),
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
            "errin": net.errin,
            "errout": net.errout,
        },
        "process": {
            "pid": os.getpid(),
            "rss_mb": round(proc_mem.rss / 1e6, 2),
            "vms_mb": round(proc_mem.vms / 1e6, 2),
            "cpu_percent": proc_cpu,
            "threads": proc_threads,
            "open_fds": proc_fds,
            "open_connections": proc_conns,
        },
    }


@router.get("/sessions")
async def sessions_overview():
    active = [s for s in _sessions if s not in _completed]
    completed = list(_completed)

    rows = []
    for sid in list(_sessions.keys()):
        log = _event_log.get(sid, [])
        event_count = len(log)
        last_event = None
        last_type = None
        agents_seen: set[str] = set()
        goal = None
        founder_id = None
        started_at = None

        for _, ev in log:
            t = ev.get("type", "")
            if t == "goal_start":
                goal = ev.get("goal", "")[:120]
                founder_id = ev.get("founder_id")
                started_at = ev.get("ts")
            if "agent" in ev:
                agents_seen.add(ev["agent"])
            last_type = t

        if log:
            last_event = log[-1][1].get("type")

        rows.append({
            "session_id": sid,
            "status": "completed" if sid in _completed else "running",
            "goal": goal,
            "founder_id": founder_id,
            "agents_seen": sorted(agents_seen),
            "event_count": event_count,
            "queue_depth": _sessions[sid].qsize() if sid in _sessions else 0,
            "last_event": last_event,
            "steer_messages": len(_steer.get(sid, [])),
        })

    rows.sort(key=lambda r: (r["status"] == "completed", r["session_id"]))

    return {
        "total": len(_sessions),
        "active": len(active),
        "completed": len(completed),
        "sessions": rows,
    }


@router.get("/sessions/{session_id}/events")
async def session_events(session_id: str, limit: int = 200):
    log = _event_log.get(session_id)
    if log is None:
        raise HTTPException(status_code=404, detail="session not found")
    events = [{"id": eid, **ev} for eid, ev in log[-limit:]]
    return {
        "session_id": session_id,
        "total_events": len(log),
        "returned": len(events),
        "events": events,
    }


@router.get("/agents")
async def agents_activity():
    agent_stats: dict[str, dict] = {}

    for sid, log in _event_log.items():
        status = "completed" if sid in _completed else "running"
        for _, ev in log:
            agent = ev.get("agent")
            if not agent:
                continue
            if agent not in agent_stats:
                agent_stats[agent] = {
                    "agent": agent,
                    "runs": 0,
                    "errors": 0,
                    "sessions": set(),
                    "last_status": None,
                }
            s = agent_stats[agent]
            s["sessions"].add(sid)
            t = ev.get("type", "")
            if t == "agent_start":
                s["runs"] += 1
            elif t == "agent_error":
                s["errors"] += 1
            if t in ("agent_start", "agent_done", "agent_error"):
                s["last_status"] = t

    result = []
    for s in agent_stats.values():
        result.append({
            **s,
            "sessions": sorted(s["sessions"]),
            "session_count": len(s["sessions"]),
        })
    result.sort(key=lambda x: -x["runs"])
    return {"agents": result}


@router.get("/logs")
async def recent_logs(lines: int = 200):
    log_file = "server.log"
    if not os.path.exists(log_file):
        # Try journald
        try:
            out = subprocess.check_output(
                ["journalctl", "-u", "astra*", "--no-pager", f"-n{lines}"],
                stderr=subprocess.DEVNULL, text=True
            )
            return {"source": "journald", "lines": out.strip().splitlines()[-lines:]}
        except Exception:
            return {"source": "none", "lines": []}

    with open(log_file) as f:
        all_lines = f.readlines()
    tail = [l.rstrip() for l in all_lines[-lines:]]
    return {"source": log_file, "total_lines": len(all_lines), "lines": tail}


@router.get("/redis")
async def redis_info():
    try:
        import redis.asyncio as aioredis
        from backend.config import settings
        r = aioredis.from_url(settings.redis_url)
        info = await r.info()
        await r.aclose()
        return {
            "connected": True,
            "version": info.get("redis_version"),
            "uptime_seconds": info.get("uptime_in_seconds"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_mb": round(info.get("used_memory", 0) / 1e6, 2),
            "used_memory_peak_mb": round(info.get("used_memory_peak", 0) / 1e6, 2),
            "total_commands_processed": info.get("total_commands_processed"),
            "total_connections_received": info.get("total_connections_received"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
            "role": info.get("role"),
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.get("/asyncio")
async def asyncio_stats():
    loop = asyncio.get_event_loop()
    all_tasks = asyncio.all_tasks(loop)
    task_list = []
    for t in all_tasks:
        coro = t.get_coro()
        task_list.append({
            "name": t.get_name(),
            "done": t.done(),
            "cancelled": t.cancelled(),
            "coro": getattr(coro, "__qualname__", str(coro)),
        })
    task_list.sort(key=lambda x: x["name"])
    return {
        "total_tasks": len(task_list),
        "running": sum(1 for t in task_list if not t["done"]),
        "tasks": task_list,
    }


@router.get("/env")
async def env_check():
    """Show which env vars are set (values redacted)."""
    keys = [
        "SUPABASE_URL", "SUPABASE_KEY", "REDIS_URL",
        "AGENT_MODEL_BASE_URL", "AGENT_MODEL_NAME", "AGENT_MODEL_API_KEY",
        "PLANNER_MODEL_BASE_URL", "PLANNER_MODEL_NAME", "PLANNER_MODEL_API_KEY",
        "DEEPINFRA_API_KEY", "VERCEL_TOKEN", "GITHUB_TOKEN",
        "CLOUDFLARE_API_TOKEN", "COMPOSIO_API_KEY",
        "CLERK_SECRET_KEY", "SENDGRID_API_KEY", "OBSIDIAN_VAULT",
    ]
    result = {}
    for k in keys:
        v = os.environ.get(k, "")
        if v:
            result[k] = f"{v[:6]}...{v[-4:]}" if len(v) > 10 else "***set***"
        else:
            result[k] = "NOT SET"
    return result


@router.get("/git")
async def git_status():
    def _run(cmd):
        try:
            return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, cwd="/opt/astra").strip()
        except Exception:
            try:
                return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
            except Exception:
                return None

    return {
        "branch": _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "commit": _run(["git", "rev-parse", "HEAD"]),
        "commit_short": _run(["git", "rev-parse", "--short", "HEAD"]),
        "commit_message": _run(["git", "log", "-1", "--pretty=%s"]),
        "commit_date": _run(["git", "log", "-1", "--pretty=%ci"]),
        "origin_commit": _run(["git", "rev-parse", "origin/main"]),
        "dirty": _run(["git", "status", "--porcelain"]) != "",
        "recent_commits": (_run(["git", "log", "--oneline", "-10"]) or "").splitlines(),
    }
