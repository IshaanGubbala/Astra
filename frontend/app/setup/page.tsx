"use client";

import { useState, useEffect } from "react";
import { setupAccounts, getSetupStatus, SetupStatus } from "@/lib/api";

const SERVICES = [
  { key: "github", label: "GitHub", icon: "🐙", desc: "Repo scaffolding, code deploys" },
  { key: "vercel", label: "Vercel", icon: "▲", desc: "Landing page hosting" },
  { key: "sendgrid", label: "SendGrid", icon: "✉️", desc: "Email campaigns" },
  { key: "instagram", label: "Instagram", icon: "📸", desc: "Reels + story publishing", oauth: true },
  { key: "tiktok", label: "TikTok", icon: "🎵", desc: "Video publishing", oauth: true },
  { key: "meta_ads", label: "Meta Ads", icon: "📢", desc: "Paid social campaigns", oauth: true },
];

const COMPOSIO_APPS = [
  { key: "gmail", label: "Gmail", icon: "📧", desc: "Send from your real inbox" },
  { key: "linkedin", label: "LinkedIn", icon: "💼", desc: "Post announcements" },
  { key: "twitter", label: "Twitter/X", icon: "🐦", desc: "Tweet launches" },
  { key: "googlecalendar", label: "Calendar", icon: "📅", desc: "Schedule investor meetings" },
  { key: "notion", label: "Notion", icon: "📝", desc: "Update company wiki" },
  { key: "linear", label: "Linear", icon: "📋", desc: "Track dev issues" },
  { key: "github", label: "GitHub (PRs)", icon: "🔀", desc: "Open PRs & issues" },
];

export default function SetupPage() {
  const [founderId, setFounderId] = useState("founder_001");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [summary, setSummary] = useState<string[]>([]);
  const [composioUrls, setComposioUrls] = useState<Record<string, string> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fetching, setFetching] = useState(false);

  async function fetchStatus() {
    if (!founderId.trim()) return;
    setFetching(true);
    try {
      const s = await getSetupStatus(founderId);
      setStatus(s);
    } catch {
      // founder may not exist yet
    } finally {
      setFetching(false);
    }
  }

  useEffect(() => {
    fetchStatus();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleProvision(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !password) return;
    setLoading(true);
    setError(null);
    setSummary([]);
    try {
      const result = await setupAccounts(founderId, email, password);
      setSummary(result.summary ?? []);
      if (result.composio_oauth_urls && !result.composio_oauth_urls.error) {
        setComposioUrls(result.composio_oauth_urls);
      }
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Provisioning failed");
    } finally {
      setLoading(false);
    }
  }

  const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  return (
    <div className="flex flex-col gap-10 max-w-2xl">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-white">Connect Accounts</h1>
        <p className="text-zinc-400">
          Astra needs API access to act on your behalf. Provide your credentials once — they're stored encrypted per founder.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <label className="text-zinc-300 text-sm font-semibold">Founder ID</label>
        <div className="flex gap-2">
          <input
            value={founderId}
            onChange={(e) => setFounderId(e.target.value)}
            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-200 text-sm focus:border-violet-500 focus:outline-none"
            placeholder="founder_001"
          />
          <button
            onClick={fetchStatus}
            disabled={fetching}
            className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:border-zinc-500 disabled:opacity-50"
          >
            {fetching ? "…" : "Check"}
          </button>
        </div>
      </div>

      {status && (
        <div className="flex flex-col gap-3">
          <h2 className="text-zinc-300 font-semibold text-sm">Connection Status</h2>
          <div className="grid grid-cols-3 gap-3">
            {SERVICES.map((svc) => {
              const connected = status[svc.key as keyof SetupStatus];
              return (
                <div
                  key={svc.key}
                  className={`rounded-xl border p-4 flex flex-col gap-2 ${
                    connected
                      ? "border-green-800 bg-green-950/20"
                      : "border-zinc-800 bg-zinc-900/50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xl">{svc.icon}</span>
                    <span className={`text-xs font-mono ${connected ? "text-green-400" : "text-zinc-600"}`}>
                      {connected ? "✓" : "–"}
                    </span>
                  </div>
                  <p className="font-semibold text-zinc-200 text-sm">{svc.label}</p>
                  <p className="text-zinc-500 text-xs">{svc.desc}</p>
                  {svc.oauth && !connected && (
                    <a
                      href={`${API_BASE}/oauth/${svc.key.replace("_ads", "")}?founder_id=${founderId}`}
                      className="text-xs text-violet-400 hover:underline mt-1"
                    >
                      Connect via OAuth →
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <form onSubmit={handleProvision} className="flex flex-col gap-4 border-t border-zinc-800 pt-6">
        <h2 className="text-zinc-300 font-semibold">Auto-provision GitHub, Vercel & SendGrid</h2>
        <p className="text-zinc-500 text-sm">
          Astra will create or connect accounts using your email and password via a headless browser. You may still need to verify your email.
        </p>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-zinc-400 text-xs">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-200 text-sm focus:border-violet-500 focus:outline-none"
              placeholder="you@example.com"
              disabled={loading}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-zinc-400 text-xs">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-zinc-200 text-sm focus:border-violet-500 focus:outline-none"
              placeholder="••••••••"
              disabled={loading}
            />
          </div>
        </div>

        {error && (
          <p className="text-red-400 text-sm rounded-lg bg-red-950/30 border border-red-800 px-4 py-2">
            {error}
          </p>
        )}

        {summary.length > 0 && (
          <ul className="flex flex-col gap-1">
            {summary.map((line, i) => (
              <li key={i} className="text-sm text-zinc-300">{line}</li>
            ))}
          </ul>
        )}

        <button
          type="submit"
          disabled={loading || !email || !password}
          className="self-start rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Provisioning (this takes ~30s)…" : "Auto-provision →"}
        </button>
      </form>

      {composioUrls && (
        <div className="flex flex-col gap-4 border-t border-zinc-800 pt-6">
          <div className="flex flex-col gap-1">
            <h2 className="text-zinc-200 font-semibold">Connect your accounts</h2>
            <p className="text-zinc-500 text-sm">
              Click each to authorize Astra. One-time OAuth — Composio stores your tokens.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {COMPOSIO_APPS.map((app) => {
              const url = composioUrls[app.key];
              const isError = !url || url.startsWith("error:");
              return (
                <a
                  key={app.key}
                  href={isError ? undefined : url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`rounded-xl border p-4 flex items-center gap-3 transition-colors ${
                    isError
                      ? "border-zinc-800 bg-zinc-900/30 opacity-50 cursor-not-allowed"
                      : "border-violet-800 bg-violet-950/20 hover:border-violet-600 hover:bg-violet-950/40"
                  }`}
                  onClick={isError ? (e) => e.preventDefault() : undefined}
                >
                  <span className="text-xl">{app.icon}</span>
                  <div className="flex flex-col gap-0.5 min-w-0">
                    <p className="font-semibold text-zinc-200 text-sm">{app.label}</p>
                    <p className="text-zinc-500 text-xs truncate">{app.desc}</p>
                  </div>
                  {!isError && (
                    <span className="ml-auto text-violet-400 text-xs whitespace-nowrap">Connect →</span>
                  )}
                </a>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
