"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getSessions, deleteSession, SessionRecord } from "@/lib/history";
import { AGENT_LABELS } from "@/lib/api";

function timeAgo(ts: number): string {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  const hrs = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (hrs < 24) return `${hrs}h ago`;
  return `${days}d ago`;
}

function StatusBadge({ status }: { status: SessionRecord["status"] }) {
  return (
    <span className={`site-pill px-2 py-1 text-xs ${
      status === "done"    ? "text-green-400 border-green-800/60 bg-green-950/30" :
      status === "error"  ? "text-red-400 border-red-800/60 bg-red-950/30" :
                            "text-indigo-300 border-indigo-800/60 bg-indigo-950/30"
    }`}>
      {status === "done" ? "✦ done" : status === "error" ? "error" : "running"}
    </span>
  );
}

export default function DashboardPage() {
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setSessions(getSessions());
    setMounted(true);
  }, []);

  function remove(id: string) {
    deleteSession(id);
    setSessions(getSessions());
  }

  if (!mounted) return null;

  return (
    <div className="flex flex-col gap-10">
      <section className="flex flex-col gap-5">
        <div className="eyebrow">Dashboard</div>
        <div className="flex items-end justify-between gap-4 flex-wrap">
          <h1 className="text-[clamp(40px,5vw,80px)] leading-[0.95]">
            Your companies.
          </h1>
          <Link href="/" className="site-btn site-btn-primary px-6 self-end">
            New goal →
          </Link>
        </div>
        <p className="lede">
          Every goal you&rsquo;ve run, with links to everything Astra built.
        </p>
      </section>

      {sessions.length === 0 ? (
        <div className="site-card p-10 flex flex-col items-center gap-5 text-center">
          <span className="text-4xl">✦</span>
          <div>
            <p className="text-lg text-white">No goals yet.</p>
            <p className="mt-2 text-sm text-[var(--fg-dim)]">
              Submit your first goal and Astra will build your company here.
            </p>
          </div>
          <Link href="/" className="site-btn site-btn-primary px-6">
            Launch your first goal →
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {sessions.map((s) => (
            <div key={s.sessionId} className="site-card p-5 sm:p-6 flex flex-col gap-4">
              {/* Header row */}
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="flex flex-col gap-1.5 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    {s.companyName && (
                      <span className="text-lg font-semibold text-white">{s.companyName}</span>
                    )}
                    <StatusBadge status={s.status} />
                    <span className="site-label">{timeAgo(s.startedAt)}</span>
                  </div>
                  <p className="text-sm text-[var(--fg-dim)] line-clamp-2 max-w-2xl">
                    {s.instruction}
                  </p>
                  <p className="font-mono text-xs text-[var(--fg-mute)]">{s.sessionId}</p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <Link
                    href={`/goal/${s.sessionId}?instruction=${encodeURIComponent(s.instruction)}`}
                    className="site-btn site-btn-ghost px-4 text-sm"
                  >
                    View →
                  </Link>
                  <button
                    onClick={() => remove(s.sessionId)}
                    className="site-btn site-btn-ghost px-3 text-sm text-[var(--fg-mute)] hover:text-red-400"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Artifacts */}
              {s.artifacts.length > 0 && (
                <div className="flex flex-wrap gap-2 border-t border-[var(--line)] pt-4">
                  {s.artifacts.map((art, i) =>
                    art.href ? (
                      <a key={i} href={art.href} target="_blank" rel="noopener noreferrer"
                        className="flex items-center gap-2 rounded-lg border border-[rgba(255,255,255,0.09)] bg-[rgba(255,255,255,0.03)] px-3 py-1.5 text-xs text-indigo-300 hover:border-indigo-500/40 hover:bg-[rgba(99,102,241,0.08)] transition-all">
                        <span>{art.icon}</span>
                        <span>{art.label}</span>
                        <span className="opacity-50">↗</span>
                      </a>
                    ) : (
                      <div key={i} className="flex items-center gap-2 rounded-lg border border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.02)] px-3 py-1.5 text-xs text-[var(--fg-dim)]">
                        <span>{art.icon}</span>
                        <span>{art.label}</span>
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
