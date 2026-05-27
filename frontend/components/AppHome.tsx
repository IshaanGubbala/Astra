"use client";

import { useState, useSyncExternalStore } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useUser, SignInButton } from "@clerk/nextjs";
import { submitGoal, AGENT_LABELS, AGENT_ORDER } from "@/lib/api";
import { getSessionSnapshot, saveSession, subscribeSessions } from "@/lib/history";
import LiquidGlass from "@/components/LiquidGlass";
import ThemeToggle from "@/components/ThemeToggle";
import { GoalWorkspace } from "@/components/GoalWorkspace";

import type { SessionRecord } from "@/lib/history";

const EMPTY_RECENT_SESSIONS: SessionRecord[] = [];

const STACK_OPTIONS = {
  frontend: ["Next.js", "React + Vite", "SvelteKit", "Remix"],
  backend: ["FastAPI", "Express / Node", "Django", "Serverless"],
  database: ["Supabase (Postgres)", "PlanetScale (MySQL)", "MongoDB", "SQLite"],
  auth: ["Clerk", "Supabase Auth", "NextAuth", "Custom JWT"],
};

const STARTER_PROMPTS = [
  {
    title: "Waitlist SaaS",
    prompt: "Build a waitlist SaaS for creators — landing page, Next.js app, Supabase DB, Clerk auth, Vercel deploy.",
  },
  {
    title: "Invoice tool",
    prompt: "Launch a B2B invoice automation tool — repo, database, auth, landing page, three investor emails.",
  },
  {
    title: "Matching platform",
    prompt: "Build a real-time co-founder matching platform with live URL, auth, and a pitch deck PDF.",
  },
];

function trimGoalLabel(value: string, fallback: string): string {
  const clean = value.trim();
  if (!clean) return fallback;
  return clean.length > 84 ? `${clean.slice(0, 81).trimEnd()}…` : clean;
}

function buildPlanTracks(instruction: string, stack: { frontend: string; backend: string; database: string; auth: string }) {
  const lower = instruction.toLowerCase();
  const tracks = [
    {
      title: "Build surface",
      detail: lower.includes("landing page")
        ? "Landing page, visual system, and first-run product shell."
        : "Primary user-facing product surface and first usable flow.",
    },
    {
      title: "Application stack",
      detail: `${stack.frontend} on ${stack.backend} with ${stack.database}.`,
    },
    {
      title: "Accounts and data",
      detail: `${stack.auth} for auth, core schema setup, and persisted product state.`,
    },
  ];

  if (lower.includes("deploy") || lower.includes("vercel")) {
    tracks.push({
      title: "Deployment",
      detail: "Hosting, environment wiring, and production deployment path.",
    });
  } else {
    tracks.push({
      title: "Delivery",
      detail: "Repo structure, environment setup, and handoff path for shipping.",
    });
  }

  if (lower.includes("email") || lower.includes("social") || lower.includes("marketing") || lower.includes("waitlist")) {
    tracks.push({
      title: "Launch distribution",
      detail: "Acquisition copy, outbound assets, and launch messaging.",
    });
  }

  return tracks.slice(0, 5);
}

function buildAgentFocus(instruction: string) {
  const lower = instruction.toLowerCase();
  const focus = ["Research", "Technical", "Web"];
  if (lower.includes("landing page") || lower.includes("brand")) focus.push("Design");
  if (lower.includes("email") || lower.includes("social") || lower.includes("marketing") || lower.includes("waitlist")) focus.push("Marketing");
  if (lower.includes("outreach") || lower.includes("sales")) focus.push("Sales");
  if (lower.includes("deploy") || lower.includes("ops")) focus.push("Ops");
  if (lower.includes("policy") || lower.includes("compliance") || lower.includes("legal")) focus.push("Legal");
  return [...new Set(focus)].slice(0, 5);
}

function getStatusLabel(status: "running" | "done" | "error") {
  if (status === "done") return "Ready";
  if (status === "error") return "Needs retry";
  return "In progress";
}

export default function AppHome() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isSignedIn } = useUser();
  const [companyName, setCompanyName] = useState("");
  const [domain, setDomain] = useState("");
  const [instruction, setInstruction] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showStack, setShowStack] = useState(false);
  const [stack, setStack] = useState({ frontend: "Next.js", backend: "FastAPI", database: "Supabase (Postgres)", auth: "Clerk" });
  const recentSessions = useSyncExternalStore(
    subscribeSessions,
    getSessionSnapshot,
    () => EMPTY_RECENT_SESSIONS,
  );

  const runningCount = recentSessions.filter(session => session.status === "running").length;
  const completedCount = recentSessions.filter(session => session.status === "done").length;
  const errorCount = recentSessions.filter(session => session.status === "error").length;
  const artifactCount = recentSessions.reduce((total, session) => total + session.artifacts.length, 0);
  const progressPct = recentSessions.length ? Math.round((completedCount / recentSessions.length) * 100) : 0;
  const latestSession = recentSessions[0];
  const draftLabel = trimGoalLabel(companyName || instruction, "Current draft");
  const planTracks = buildPlanTracks(instruction, stack);
  const agentFocus = buildAgentFocus(instruction);
  const preRunAgents = AGENT_ORDER.filter((agent) => !agent.startsWith("research_"));

  const activeSessionId = searchParams.get("session") ?? latestSession?.sessionId ?? "";
  const activeInstruction = searchParams.get("instruction") ?? latestSession?.instruction ?? "";
  const activeFounderId = searchParams.get("founder") ?? latestSession?.founderId ?? user?.id ?? "founder_001";
  const activeCompany = searchParams.get("company") ?? latestSession?.companyName ?? "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!instruction.trim()) return;
    setLoading(true);
    setError(null);
    const parts = [
      companyName.trim() && `Company name: ${companyName.trim()}.`,
      domain.trim() && `Domain: ${domain.trim()}.`,
      showStack && `Tech stack: Frontend=${stack.frontend}, Backend=${stack.backend}, Database=${stack.database}, Auth=${stack.auth}.`,
    ].filter(Boolean);
    const full = parts.length ? `${parts.join(" ")}\n\n${instruction}` : instruction;
    const founderId = user?.id ?? "anon";
    try {
      const result = await submitGoal(founderId, full);
      saveSession({ sessionId: result.session_id, founderId, companyName: companyName.trim() || instruction.slice(0, 40), instruction, startedAt: Date.now(), status: "running", artifacts: [] });
      if (typeof Notification !== "undefined" && Notification.permission === "default") Notification.requestPermission();
      router.push(`/?session=${encodeURIComponent(result.session_id)}&instruction=${encodeURIComponent(instruction)}&founder=${encodeURIComponent(founderId)}&company=${encodeURIComponent(companyName)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit goal");
      setLoading(false);
    }
  }

  if (activeSessionId) {
    return (
      <div className="site-shell" style={{ paddingTop: 48, paddingBottom: 88 }}>
        <GoalWorkspace
          sessionId={activeSessionId}
          instruction={activeInstruction}
          founderId={activeFounderId}
          company={activeCompany}
        />
      </div>
    );
  }

  return (
    <div className="site-shell" style={{ paddingTop: 48, paddingBottom: 88 }}>
      <div className="goal-workspace" style={{ width: "100%", maxWidth: 1480, margin: "0 auto", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <div style={{ width: 24, height: 24, borderRadius: 8, display: "grid", placeItems: "center", background: "rgba(168,172,178,0.92)", color: "rgba(10,14,22,0.92)", fontWeight: 600, fontSize: 12, flexShrink: 0 }}>A</div>
            <h1 style={{ fontSize: 18, fontWeight: 600, color: "var(--fg)", margin: 0 }}>
              {isSignedIn && user?.firstName ? `What are you building, ${user.firstName}?` : "What are you building?"}
            </h1>
            <span style={{ fontSize: 11, letterSpacing: "0.06em", padding: "3px 10px", borderRadius: 999, color: "var(--fg-mute)", background: "rgba(0,0,0,0.04)", border: "1px solid rgba(0,0,0,0.1)" }}>
              ready
            </span>
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <Link href="/settings" className="site-btn site-btn-ghost" aria-label="Account settings" title="Account settings" style={{ width: 36, minHeight: 34, padding: 0, fontSize: 17, lineHeight: 1 }}>⚙</Link>
              <Link href="/integrations" className="site-btn site-btn-ghost" aria-label="Integration settings" title="Integration settings" style={{ width: 36, minHeight: 34, padding: 0, fontSize: 17, lineHeight: 1 }}>⌘</Link>
              <button
                type="button"
                onClick={() => {
                  if (recentSessions.length === 0) return;
                  if (confirm("Clear all session history?")) {
                    localStorage.removeItem("astra_sessions");
                    window.location.reload();
                  }
                }}
                className="site-btn site-btn-ghost"
                style={{ minHeight: 34, padding: "0 12px", fontSize: 12, color: "#C97070" }}
              >
                Clear sessions
              </button>
              <ThemeToggle />
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ flex: 1, height: 3, borderRadius: 999, background: "rgba(0,0,0,0.08)", overflow: "hidden" }}>
              <div style={{ height: "100%", width: "0%", borderRadius: 999, background: "#2563EB" }} />
            </div>
            <span style={{ fontSize: 11, color: "var(--fg-dim)", flexShrink: 0, fontFamily: "var(--font-jetbrains-mono)" }}>0/{preRunAgents.length}</span>
          </div>
        </div>

        <div className="goal-workspace-grid" style={{ display: "grid", gridTemplateColumns: "minmax(260px, 320px) minmax(0, 1fr)", gap: 18, alignItems: "stretch" }}>
          <LiquidGlass style={{ minWidth: 0 }} contentStyle={{ padding: "12px", display: "flex", flexDirection: "column", gap: 4, minHeight: 620 }}>
            {preRunAgents.map((agent, index) => (
              <div
                key={agent}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 12px",
                  borderRadius: 24,
                  border: index === 0 ? "1px solid rgba(180,205,228,0.22)" : "1px solid transparent",
                  background: index === 0 ? "rgba(180,205,228,0.10)" : "transparent",
                }}
              >
                <div style={{ position: "relative", width: 28, height: 28, flexShrink: 0 }}>
                  <svg viewBox="0 0 28 28" style={{ width: 28, height: 28 }}>
                    <circle cx="14" cy="14" r="11" fill="none" stroke="rgba(0,0,0,0.1)" strokeWidth="2.5" />
                  </svg>
                  <span style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, color: "var(--fg-mute)" }}>{index + 1}</span>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500, color: index === 0 ? "var(--fg)" : "var(--fg-mute)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {AGENT_LABELS[agent] ?? agent}
                  </div>
                  <div style={{ fontSize: 10, color: "rgba(0,0,0,0.25)", textTransform: "uppercase", letterSpacing: "0.06em" }}>waiting</div>
                </div>
              </div>
            ))}
          </LiquidGlass>

          <LiquidGlass style={{ minWidth: 0 }} contentStyle={{ padding: "32px", minHeight: 620, display: "flex", flexDirection: "column", gap: 18 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ fontSize: 20 }}>A</span>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: 15, fontWeight: 600, color: "var(--fg)" }}>New run</span>
                  <span style={{ fontSize: 10, fontFamily: "var(--font-jetbrains-mono)", letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--fg-mute)" }}>ready</span>
                </div>
                <p style={{ margin: "2px 0 0", fontSize: 11, color: "var(--fg-mute)", lineHeight: 1.4 }}>
                  Describe the product. Astra will split the work across the full agent team.
                </p>
              </div>
              <div style={{ position: "relative", width: 40, height: 40, flexShrink: 0 }}>
                <svg viewBox="0 0 40 40">
                  <circle cx="20" cy="20" r="17" fill="none" stroke="rgba(0,0,0,0.08)" strokeWidth="3" />
                </svg>
                <span style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 600, fontFamily: "var(--font-jetbrains-mono)", color: "var(--fg-mute)" }}>0%</span>
              </div>
            </div>

            <div style={{ height: 3, borderRadius: 999, background: "rgba(0,0,0,0.08)", overflow: "hidden" }}>
              <div style={{ height: "100%", width: "0%", borderRadius: 999, background: "#2563EB" }} />
            </div>

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12, flex: 1 }}>
              <div style={{ display: "grid", gridTemplateColumns: "1.15fr 0.85fr", gap: 12 }}>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label className="site-label">Company</label>
                  <input value={companyName} onChange={e => setCompanyName(e.target.value)} className="site-input" style={{ padding: "9px 12px", fontSize: 14 }} placeholder="Astra" disabled={loading} />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label className="site-label">Domain</label>
                  <input value={domain} onChange={e => setDomain(e.target.value)} className="site-input" style={{ padding: "9px 12px", fontSize: 14 }} placeholder="astra.ai" disabled={loading} />
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <label className="site-label">Goal</label>
                <textarea
                  value={instruction}
                  onChange={e => setInstruction(e.target.value)}
                  placeholder="Build a SaaS for indie hackers to track MRR — landing page, GitHub repo, Supabase backend, Clerk auth, Vercel deploy."
                  rows={6}
                  disabled={loading}
                  className="site-textarea"
                  style={{ padding: "12px 14px", fontSize: 14, lineHeight: 1.65, resize: "none" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <p className="site-label">Starter prompts</p>
                {STARTER_PROMPTS.map((item) => (
                  <button
                    key={item.title}
                    type="button"
                    onClick={() => setInstruction(item.prompt)}
                    disabled={loading}
                    style={{ textAlign: "left", fontSize: 12, color: "var(--fg-mute)", background: "none", border: "none", padding: "1px 0", cursor: "pointer", lineHeight: 1.6 }}
                  >
                    · {item.title}
                  </button>
                ))}
              </div>

              <div style={{ border: "1px solid var(--line)", borderRadius: 24, padding: "10px 14px" }}>
                <button type="button" onClick={() => setShowStack(v => !v)} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
                  <span className="site-label">Tech stack</span>
                  <span style={{ fontSize: 10, color: "var(--fg-mute)" }}>{showStack ? "▲" : "▼"}</span>
                </button>
                {showStack && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 14 }}>
                    {(Object.entries(STACK_OPTIONS) as [string, string[]][]).map(([key, opts]) => (
                      <div key={key} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        <label className="site-label">{key}</label>
                        <select value={stack[key as keyof typeof stack]} onChange={e => setStack(p => ({ ...p, [key]: e.target.value }))} disabled={loading} className="site-input" style={{ padding: "7px 10px", fontSize: 12, background: "linear-gradient(135deg, rgba(255,255,255,0.08), rgba(180,205,228,0.04)), var(--glass-hi)" }}>
                          {opts.map(o => <option key={o} value={o} style={{ background: "#0b0e14" }}>{o}</option>)}
                        </select>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", paddingTop: 4 }}>
                {isSignedIn ? (
                  <button type="submit" disabled={loading || !instruction.trim()} className="site-btn site-btn-primary" style={{ padding: "0 24px", fontSize: 14 }}>
                    {loading ? "Launching…" : "Launch Astra →"}
                  </button>
                ) : (
                  <SignInButton mode="modal">
                    <button type="button" className="site-btn site-btn-primary" style={{ padding: "0 24px", fontSize: 14 }}>Sign in to launch →</button>
                  </SignInButton>
                )}
              </div>

              {error && <p style={{ borderRadius: 24, border: "1px solid rgba(220,38,38,0.4)", background: "rgba(127,29,29,0.2)", padding: "10px 14px", fontSize: 13, color: "#fca5a5" }}>{error}</p>}
            </form>
          </LiquidGlass>
        </div>

        <div className="blob-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 14, alignItems: "stretch" }}>
          <LiquidGlass contentStyle={{ padding: "30px 32px", display: "flex", flexDirection: "column", gap: 24, minHeight: 420 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span className="site-label">Progress</span>
              <h3 style={{ fontSize: 18 }}>Run health</h3>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 18, flex: 1 }}>
              <div style={{ padding: "14px 14px", borderRadius: 20, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(176,180,186,0.10)", display: "grid", gap: 8 }}>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
                  <div style={{ display: "grid", gap: 5, minWidth: 0 }}>
                    <span style={{ fontSize: 10, color: "var(--fg-mute)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Latest run</span>
                    <span style={{ fontSize: 14, color: "var(--fg)", lineHeight: 1.45 }}>
                      {latestSession ? trimGoalLabel(latestSession.companyName, "Untitled run") : draftLabel}
                    </span>
                  </div>
                  <span style={{ padding: "5px 9px", borderRadius: 999, border: "1px solid rgba(176,180,186,0.14)", background: "rgba(255,255,255,0.04)", color: "var(--fg-mute)", fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase", whiteSpace: "nowrap" }}>
                    {latestSession ? getStatusLabel(latestSession.status) : "Not started"}
                  </span>
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, color: "var(--fg-dim)", fontSize: 12 }}>
                  <span>{latestSession ? `${latestSession.artifacts.length} artifacts captured` : "No saved artifacts yet"}</span>
                  {latestSession && <span style={{ fontFamily: "var(--font-jetbrains-mono)" }}>#{latestSession.sessionId.slice(0, 8)}</span>}
                </div>
                {latestSession && (
                  <button type="button" onClick={() => router.push(`/?session=${encodeURIComponent(latestSession.sessionId)}&instruction=${encodeURIComponent(latestSession.instruction)}&founder=${encodeURIComponent(latestSession.founderId)}&company=${encodeURIComponent(latestSession.companyName)}`)} className="site-btn site-btn-primary" style={{ width: "fit-content", padding: "0 18px" }}>
                    Open latest →
                  </button>
                )}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
                {[
                  ["Saved", recentSessions.length],
                  ["Running", runningCount],
                  ["Done", completedCount],
                  ["Errors", errorCount],
                ].map(([label, value]) => (
                  <div key={label} style={{ padding: "10px 10px", borderRadius: 18, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(176,180,186,0.10)", display: "flex", flexDirection: "column", gap: 3 }}>
                    <span style={{ fontSize: 17, lineHeight: 1.1, color: "var(--fg)" }}>{value}</span>
                    <span style={{ fontSize: 10, color: "var(--fg-mute)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</span>
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
                  <span style={{ fontSize: 12, color: "var(--fg-dim)" }}>Saved run completion</span>
                  <span style={{ fontSize: 11, color: "var(--fg-mute)", fontFamily: "var(--font-jetbrains-mono)" }}>{progressPct}%</span>
                </div>
                <div style={{ height: 7, borderRadius: 999, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(176,180,186,0.10)", overflow: "hidden" }}>
                  <div style={{ width: `${progressPct}%`, height: "100%", borderRadius: 999, background: "var(--action)", transition: "width 0.3s ease" }} />
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div style={{ padding: "12px 13px", borderRadius: 18, background: "rgba(255,255,255,0.025)", border: "1px solid rgba(176,180,186,0.10)", display: "grid", gap: 3 }}>
                  <span style={{ fontSize: 10, color: "var(--fg-mute)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Artifacts collected</span>
                  <span style={{ fontSize: 14, color: "var(--fg)" }}>{artifactCount} across saved runs</span>
                </div>
                <div style={{ padding: "12px 13px", borderRadius: 18, background: "rgba(255,255,255,0.025)", border: "1px solid rgba(176,180,186,0.10)", display: "grid", gap: 3 }}>
                  <span style={{ fontSize: 10, color: "var(--fg-mute)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Current focus</span>
                  <span style={{ fontSize: 14, color: "var(--fg)" }}>{agentFocus.join(" · ")}</span>
                </div>
              </div>
            </div>
          </LiquidGlass>

          <LiquidGlass contentStyle={{ padding: "30px 32px", display: "flex", flexDirection: "column", gap: 24, minHeight: 420 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span className="site-label">Plan</span>
              <h3 style={{ fontSize: 18 }}>Current build plan</h3>
            </div>
            <div style={{ display: "grid", gap: 16, flex: 1 }}>
              <div style={{ padding: "13px 14px", borderRadius: 20, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(176,180,186,0.10)", display: "grid", gap: 5 }}>
                <span style={{ fontSize: 10, color: "var(--fg-mute)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Build target</span>
                <span style={{ fontSize: 14, color: "var(--fg)", lineHeight: 1.55 }}>
                  {instruction.trim() ? trimGoalLabel(instruction, "Describe the product you want built.") : "Describe the product you want built."}
                </span>
              </div>
              <div style={{ padding: "11px 13px", borderRadius: 22, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(176,180,186,0.10)", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {Object.entries(stack).map(([key, value]) => (
                  <div key={key} style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0 }}>
                    <span style={{ fontSize: 10, color: "var(--fg-mute)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{key}</span>
                    <span style={{ fontSize: 12, color: "var(--fg)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{value}</span>
                  </div>
                ))}
              </div>
              <div style={{ display: "grid", gap: 8 }}>
                {planTracks.map((step, index) => (
                  <div key={step.title} style={{ display: "grid", gridTemplateColumns: "22px 1fr", alignItems: "flex-start", gap: 10 }}>
                    <span style={{ width: 22, height: 22, borderRadius: 999, display: "grid", placeItems: "center", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(176,180,186,0.10)", color: "var(--fg-mute)", fontSize: 10, fontFamily: "var(--font-jetbrains-mono)" }}>{index + 1}</span>
                    <div style={{ display: "grid", gap: 3 }}>
                      <span style={{ fontSize: 12, color: "var(--fg)" }}>{step.title}</span>
                      <span style={{ fontSize: 12, color: "var(--fg-dim)", lineHeight: 1.45 }}>{step.detail}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ padding: "12px 13px", borderRadius: 18, background: "rgba(255,255,255,0.025)", border: "1px solid rgba(176,180,186,0.10)", display: "grid", gap: 6 }}>
                <span style={{ fontSize: 10, color: "var(--fg-mute)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Active agent lanes</span>
                <span style={{ fontSize: 13, color: "var(--fg)", lineHeight: 1.45 }}>{agentFocus.join(" · ")}</span>
              </div>
            </div>
          </LiquidGlass>

          <LiquidGlass contentStyle={{ padding: "30px 32px", display: "flex", flexDirection: "column", gap: 24, overflow: "hidden", minHeight: 420 }}>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 18 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 0 }}>
                <span className="site-label">Recent</span>
                <h3 style={{ fontSize: 18 }}>Saved sessions</h3>
              </div>
              <span style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--fg-mute)", whiteSpace: "nowrap", paddingTop: 3 }}>{recentSessions.length} saved</span>
            </div>
            <div style={{ display: "grid", gap: 12 }}>
              {recentSessions.slice(0, 4).length ? recentSessions.slice(0, 4).map((session) => (
                <button
                  key={session.sessionId}
                  type="button"
                  onClick={() => router.push(`/?session=${encodeURIComponent(session.sessionId)}&instruction=${encodeURIComponent(session.instruction)}&founder=${encodeURIComponent(session.founderId)}&company=${encodeURIComponent(session.companyName)}`)}
                  style={{ display: "flex", flexDirection: "column", alignItems: "stretch", gap: 5, padding: "11px 14px", borderRadius: 22, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(176,180,186,0.10)", textAlign: "left", overflow: "hidden" }}
                >
                  <span style={{ fontSize: 13, color: "var(--fg)", lineHeight: 1.35, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {session.companyName}
                  </span>
                  <span style={{ fontSize: 12, color: "var(--fg-dim)", lineHeight: 1.45, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {session.instruction}
                  </span>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0, color: "var(--fg-mute)", fontSize: 11 }}>
                    <span>{getStatusLabel(session.status)} · {session.artifacts.length} artifacts</span>
                    <span style={{ opacity: 0.45 }}>·</span>
                    <span style={{ fontFamily: "var(--font-jetbrains-mono)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{session.sessionId.slice(0, 6)}</span>
                  </div>
                </button>
              )) : (
                <div style={{ padding: "14px 12px", borderRadius: 22, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(176,180,186,0.10)", color: "var(--fg-mute)", fontSize: 13, lineHeight: 1.6 }}>
                  Launch a run and it will appear here.
                </div>
              )}
            </div>
          </LiquidGlass>
        </div>
      </div>
    </div>
  );
}
