"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { UserButton } from "@clerk/nextjs";
import { getSessions, deleteSession, SessionRecord } from "@/lib/history";

function timeAgo(ts: number): string {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  const hrs = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (mins < 1) return "now";
  if (mins < 60) return `${mins}m`;
  if (hrs < 24) return `${hrs}h`;
  return `${days}d`;
}

function groupSessions(sessions: SessionRecord[]): Record<string, SessionRecord[]> {
  const now = Date.now();
  const today = new Date(); today.setHours(0,0,0,0);
  const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1);
  const weekAgo = new Date(today); weekAgo.setDate(weekAgo.getDate() - 7);

  const groups: Record<string, SessionRecord[]> = {
    Today: [], Yesterday: [], "This week": [], Older: [],
  };
  for (const s of sessions) {
    const d = new Date(s.startedAt); d.setHours(0,0,0,0);
    if (d >= today) groups.Today.push(s);
    else if (d >= yesterday) groups.Yesterday.push(s);
    else if (d >= weekAgo) groups["This week"].push(s);
    else groups.Older.push(s);
  }
  return groups;
}

function statusDot(status: SessionRecord["status"]) {
  if (status === "done") return "bg-green-400";
  if (status === "error") return "bg-red-400";
  return "bg-[var(--star)] animate-pulse";
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setSessions(getSessions());
    setMounted(true);
    // Poll for updates while sessions are running
    const id = setInterval(() => setSessions(getSessions()), 3000);
    return () => clearInterval(id);
  }, []);

  function remove(e: React.MouseEvent, id: string) {
    e.preventDefault();
    e.stopPropagation();
    deleteSession(id);
    setSessions(getSessions());
    if (pathname.includes(id)) router.push("/dashboard");
  }

  const groups = mounted ? groupSessions(sessions) : {};

  return (
    <aside style={{
      width: 260, flexShrink: 0, display: "flex", flexDirection: "column",
      borderRight: "1px solid var(--line)", background: "var(--ink-2)",
      height: "100%", overflow: "hidden",
    }}>
      {/* Brand */}
      <div style={{ padding: "18px 16px 12px", display: "flex", alignItems: "center", gap: 10, borderBottom: "1px solid var(--line)" }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
          <span style={{
            width: 22, height: 22, borderRadius: "50%", flexShrink: 0,
            background: "radial-gradient(circle, var(--fg) 0%, var(--star) 55%, transparent 75%)",
            boxShadow: "0 0 12px var(--star)",
          }} />
          <span style={{ fontSize: 13, letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--fg)", fontFamily: "var(--font-geist-sans)" }}>
            Astra
          </span>
        </Link>
      </div>

      {/* New goal button */}
      <div style={{ padding: "12px 12px 8px" }}>
        <Link href="/dashboard" className="site-btn site-btn-primary" style={{ width: "100%", borderRadius: 8, justifyContent: "center", fontSize: 13, minHeight: 36 }}>
          + New goal
        </Link>
      </div>

      {/* Session list */}
      <nav style={{ flex: 1, overflowY: "auto", padding: "4px 8px" }}>
        {!mounted || sessions.length === 0 ? (
          <div style={{ padding: "24px 8px", textAlign: "center" }}>
            <p style={{ fontSize: 12, color: "var(--fg-mute)", lineHeight: 1.6 }}>No sessions yet.<br />Run your first goal.</p>
          </div>
        ) : (
          Object.entries(groups).map(([group, items]) =>
            items.length === 0 ? null : (
              <div key={group} style={{ marginBottom: 16 }}>
                <p style={{
                  fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase",
                  color: "var(--fg-mute)", padding: "4px 8px 6px",
                  fontFamily: "var(--font-mono)",
                }}>
                  {group}
                </p>
                {items.map(s => {
                  const isActive = pathname.includes(s.sessionId);
                  const label = s.companyName || s.instruction.slice(0, 36);
                  return (
                    <Link
                      key={s.sessionId}
                      href={`/goal/${s.sessionId}?instruction=${encodeURIComponent(s.instruction)}&founder=${encodeURIComponent(s.founderId)}`}
                      style={{
                        display: "flex", alignItems: "center", gap: 8, borderRadius: 6,
                        padding: "7px 8px", textDecoration: "none", position: "relative",
                        background: isActive ? "rgba(32,96,255,0.1)" : "transparent",
                        border: isActive ? "1px solid rgba(32,96,255,0.2)" : "1px solid transparent",
                        transition: "background 0.15s, border-color 0.15s",
                      }}
                      onMouseEnter={e => { if (!isActive) (e.currentTarget as HTMLElement).style.background = "rgba(245,255,255,0.04)"; }}
                      onMouseLeave={e => { if (!isActive) (e.currentTarget as HTMLElement).style.background = "transparent"; }}
                    >
                      <span style={{ width: 6, height: 6, borderRadius: "50%", flexShrink: 0 }} className={statusDot(s.status)} />
                      <span style={{ flex: 1, fontSize: 13, color: isActive ? "var(--fg)" : "var(--fg-dim)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", lineHeight: 1.4 }}>
                        {label}
                      </span>
                      <span style={{ fontSize: 10, color: "var(--fg-mute)", flexShrink: 0, fontFamily: "var(--font-mono)" }}>
                        {timeAgo(s.startedAt)}
                      </span>
                      <button
                        onClick={e => remove(e, s.sessionId)}
                        style={{ display: "none", background: "none", border: "none", padding: "0 2px", color: "var(--fg-mute)", cursor: "pointer", fontSize: 12, lineHeight: 1 }}
                        className="sidebar-delete-btn"
                        aria-label="Delete session"
                      >✕</button>
                    </Link>
                  );
                })}
              </div>
            )
          )
        )}
      </nav>

      {/* Bottom bar */}
      <div style={{ padding: "12px 16px", borderTop: "1px solid var(--line)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <UserButton
          appearance={{ elements: { avatarBox: "w-8 h-8 rounded-full ring-1 ring-[rgba(255,255,255,0.15)]" } }}
        />
        <div style={{ display: "flex", gap: 6 }}>
          <Link href="/setup" style={{ fontSize: 12, color: "var(--fg-mute)", padding: "4px 8px", borderRadius: 6, border: "1px solid transparent", transition: "all 0.15s" }}>
            Setup
          </Link>
          <Link href="/" style={{ fontSize: 12, color: "var(--fg-mute)", padding: "4px 8px", borderRadius: 6, border: "1px solid transparent", transition: "all 0.15s" }}>
            Home
          </Link>
        </div>
      </div>
    </aside>
  );
}
