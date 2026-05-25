"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { saveServiceCredential, getComposioOAuthUrls, getSetupStatus, SetupStatus } from "@/lib/api";

const STEPS = [
  { id: "founder", label: "Founder ID" },
  { id: "github", label: "GitHub" },
  { id: "sendgrid", label: "SendGrid" },
  { id: "vercel", label: "Vercel" },
  { id: "composio", label: "Composio" },
  { id: "done", label: "Done" },
];

const COMPOSIO_APPS = [
  { key: "gmail", label: "Gmail", icon: "📧", desc: "Send from your inbox" },
  { key: "linkedin", label: "LinkedIn", icon: "💼", desc: "Post announcements" },
  { key: "twitter", label: "Twitter/X", icon: "🐦", desc: "Tweet launches (requires custom OAuth app)" },
  { key: "googlecalendar", label: "Calendar", icon: "📅", desc: "Schedule meetings" },
  { key: "notion", label: "Notion", icon: "📝", desc: "Update wiki" },
  { key: "linear", label: "Linear", icon: "📋", desc: "Track dev issues" },
  { key: "github", label: "GitHub PRs", icon: "🔀", desc: "Open PRs & issues" },
];

interface StepConfig {
  service: string;
  credKey: string;
  title: string;
  description: string;
  placeholder: string;
  createUrl: string;
  createLabel: string;
  instructions: string[];
}

const SERVICE_STEPS: StepConfig[] = [
  {
    service: "github",
    credKey: "token",
    title: "GitHub Personal Access Token",
    description: "Astra uses this to scaffold repos, push code, and open PRs on your behalf.",
    placeholder: "ghp_xxxxxxxxxxxxxxxxxxxx",
    createUrl: "https://github.com/settings/tokens/new?description=Astra+Automation&scopes=repo,workflow,write:packages",
    createLabel: "Create token on GitHub →",
    instructions: [
      "Click the link below to open GitHub token settings",
      "Set expiration to \"No expiration\" (or 1 year)",
      "Check: repo, workflow, write:packages",
      "Click Generate token, copy it here",
    ],
  },
  {
    service: "sendgrid",
    credKey: "api_key",
    title: "SendGrid API Key",
    description: "Astra uses this to send email campaigns from your SendGrid account.",
    placeholder: "SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    createUrl: "https://app.sendgrid.com/settings/api_keys",
    createLabel: "Create key on SendGrid →",
    instructions: [
      "Sign in or create a free SendGrid account",
      "Go to Settings → API Keys → Create API Key",
      "Choose Full Access",
      "Copy the key and paste it here",
    ],
  },
  {
    service: "vercel",
    credKey: "token",
    title: "Vercel Deploy Token",
    description: "Astra uses this to deploy your landing page and app to Vercel.",
    placeholder: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    createUrl: "https://vercel.com/account/tokens",
    createLabel: "Create token on Vercel →",
    instructions: [
      "Sign in or create a free Vercel account",
      "Go to Account → Tokens → Create",
      "Name it \"Astra Deploy\", no expiry",
      "Copy the token and paste it here",
    ],
  },
];

export default function SetupPage() {
  const [step, setStep] = useState(0);
  const [founderId, setFounderId] = useState("founder_001");
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [composioUrls, setComposioUrls] = useState<Record<string, string> | null>(null);
  const [composioLoading, setComposioLoading] = useState(false);
  const [status, setStatus] = useState<SetupStatus | null>(null);

  useEffect(() => {
    if (step !== STEPS.length - 1) return;
    let cancelled = false;

    (async () => {
      try {
        const s = await getSetupStatus(founderId);
        if (!cancelled) setStatus(s);
      } catch {
        // founder may not exist yet
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [step, founderId]);

  async function handleFounderNext() {
    if (!founderId.trim()) return;
    setStep(1);
  }

  async function handleServiceSave(cfg: StepConfig) {
    const val = inputs[cfg.service]?.trim();
    if (!val) { setError("Paste your " + cfg.title + " to continue."); return; }
    setSaving(true);
    setError(null);
    try {
      await saveServiceCredential(founderId, cfg.service, { [cfg.credKey]: val });
      setStep((s) => s + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleSkip() {
    setStep((s) => s + 1);
    setError(null);
  }

  async function loadComposioUrls() {
    setComposioLoading(true);
    setError(null);
    try {
      const urls = await getComposioOAuthUrls(founderId);
      setComposioUrls(urls);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load OAuth URLs");
    } finally {
      setComposioLoading(false);
    }
  }

  const currentStepId = STEPS[step]?.id;

  return (
    <div className="flex max-w-6xl flex-col gap-10">
      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
        <div className="flex flex-col gap-5">
          <div className="eyebrow">Setup</div>
          <h1 className="max-w-2xl text-[clamp(42px,4.8vw,72px)] leading-[0.94]">
            Connect your accounts.
          </h1>
          <p className="lede max-w-xl">
            Astra works best when your core services are connected once and reused everywhere.
            Add the essentials now, then finish the rest later.
          </p>

          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { label: "Founder ID", value: founderId },
              { label: "Current step", value: STEPS[step].label },
              { label: "Mode", value: step === 0 ? "start" : "continue" },
            ].map((item) => (
              <div key={item.label} className="site-card site-card-soft p-4">
                <p className="site-label">{item.label}</p>
                <p className="mt-3 text-sm text-white">{item.value}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="site-card p-5">
          <p className="site-label">Setup progress</p>
          <div className="mt-4 flex flex-col gap-3">
            <div className="flex items-center gap-1.5">
            {STEPS.map((s, i) => (
              <div key={s.id} className="flex items-center gap-1.5">
                <div
                  className={`h-2 rounded-full transition-all ${
                    i < step
                      ? "bg-green-500 w-6"
                      : i === step
                      ? "bg-blue-500 w-8"
                      : "bg-[var(--line)] w-4"
                  }`}
                />
                {i < STEPS.length - 1 && <div className="h-px w-2 bg-[var(--line)]" />}
              </div>
            ))}
            </div>
            <span className="text-xs text-[var(--fg-dim)]">{STEPS[step].label}</span>
          </div>
        </div>
      </section>

      {/* Step: Founder ID */}
      {currentStepId === "founder" && (
        <div className="site-card p-5 sm:p-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
          <div className="flex flex-col gap-3">
            <span className="site-pill px-2 py-1 text-blue-300">Step 1</span>
            <h2 className="text-[clamp(32px,3vw,52px)] leading-[0.96]">Who are you?</h2>
            <p className="text-sm leading-6 text-[var(--fg-dim)]">
              Credentials are stored encrypted per founder ID. Use the same ID everywhere in Astra.
            </p>
            <div className="site-card site-card-soft p-4">
              <p className="site-label">Why this matters</p>
              <p className="mt-3 text-sm leading-6 text-[var(--fg-dim)]">
                Astra uses the founder ID to keep service connections, setup progress, and generated assets tied to the same account.
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="site-label">Founder ID</label>
              <input
                value={founderId}
                onChange={(e) => setFounderId(e.target.value)}
                className="site-input px-4 py-3 text-sm text-white"
                placeholder="founder_001"
                onKeyDown={(e) => e.key === "Enter" && handleFounderNext()}
              />
            </div>
            <button
              onClick={handleFounderNext}
              disabled={!founderId.trim()}
              className="site-btn site-btn-primary self-start px-6"
            >
              Start setup →
            </button>
          </div>
        </div>
      )}

      {/* Steps: GitHub / SendGrid / Vercel */}
      {SERVICE_STEPS.map((cfg, i) => {
        if (currentStepId !== cfg.service) return null;
        return (
          <div key={cfg.service} className="site-card p-5 sm:p-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
            <div className="flex flex-col gap-3">
              <span className="site-pill px-2 py-1 text-blue-300">
                Step {i + 2} of {STEPS.length}
              </span>
              <h2 className="text-[clamp(30px,3vw,52px)] leading-[0.96]">{cfg.title}</h2>
              <p className="text-sm leading-6 text-[var(--fg-dim)]">{cfg.description}</p>
              <div className="site-card site-card-soft p-4">
                <p className="site-label">Instructions</p>
                <ol className="mt-3 flex flex-col gap-2">
                  {cfg.instructions.map((inst, j) => (
                    <li key={j} className="flex gap-3 text-sm text-[var(--fg-dim)]">
                      <span className="site-label w-4 shrink-0">{j + 1}.</span>
                      {inst}
                    </li>
                  ))}
                </ol>
              </div>
              <a
                href={cfg.createUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="self-start text-sm text-blue-300 underline underline-offset-2 hover:text-blue-300"
              >
                {cfg.createLabel}
              </a>
            </div>

            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <label className="site-label">
                  Paste {cfg.title}
                </label>
                <input
                  value={inputs[cfg.service] ?? ""}
                  onChange={(e) => setInputs((p) => ({ ...p, [cfg.service]: e.target.value }))}
                  className="site-input px-4 py-3 text-sm font-mono text-white"
                  placeholder={cfg.placeholder}
                  onKeyDown={(e) => e.key === "Enter" && handleServiceSave(cfg)}
                />
              </div>

              {error && (
                <p className="rounded-2xl border border-red-900/70 bg-red-950/30 px-4 py-3 text-sm text-red-300">
                  {error}
                </p>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => handleServiceSave(cfg)}
                  disabled={saving || !inputs[cfg.service]?.trim()}
                  className="site-btn site-btn-primary px-6"
                >
                  {saving ? "Saving…" : "Save & continue →"}
                </button>
                <button
                  onClick={handleSkip}
                  disabled={saving}
                  className="site-btn site-btn-ghost px-5 text-sm"
                >
                  Skip for now
                </button>
              </div>
            </div>
          </div>
        );
      })}

      {/* Step: Composio OAuth */}
      {currentStepId === "composio" && (
        <div className="site-card p-5 sm:p-6 grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div className="flex flex-col gap-3">
            <span className="site-pill px-2 py-1 text-blue-300">Step 5 of {STEPS.length}</span>
            <h2 className="text-[clamp(30px,3vw,52px)] leading-[0.96]">Connect your accounts</h2>
            <p className="text-sm leading-6 text-[var(--fg-dim)]">
              Astra uses Composio to act on your behalf. Send emails, post updates, manage calendars, and connect the rest of your workflow from one place.
            </p>
            <div className="site-card site-card-soft p-4">
              <p className="site-label">Composio</p>
              <p className="mt-3 text-sm leading-6 text-[var(--fg-dim)]">
                Paste the API key first, then authorize the apps you want Astra to use.
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-4">
            <div className="site-card site-card-soft flex flex-col gap-3 p-4">
              <div className="flex flex-col gap-1">
                <p className="text-sm font-medium text-white">Composio API Key</p>
                <p className="text-xs text-[var(--fg-mute)]">
                  Free at{" "}
                  <a href="https://app.composio.dev/settings" target="_blank" rel="noopener noreferrer" className="text-blue-300 hover:underline">
                    app.composio.dev/settings
                  </a>
                </p>
              </div>
              <div className="flex gap-2">
                <input
                  value={inputs["composio_api_key"] ?? ""}
                  onChange={(e) => setInputs((p) => ({ ...p, composio_api_key: e.target.value }))}
                  className="site-input flex-1 px-4 py-3 text-sm font-mono text-white"
                  placeholder="api_key_..."
                />
                <button
                  onClick={async () => {
                    const key = inputs["composio_api_key"]?.trim();
                    if (!key) return;
                    setSaving(true);
                    setError(null);
                    try {
                      await saveServiceCredential(founderId, "composio", { api_key: key });
                      setSaving(false);
                    } catch (e) {
                      setError(e instanceof Error ? e.message : "Save failed");
                      setSaving(false);
                    }
                  }}
                  disabled={saving || !inputs["composio_api_key"]?.trim()}
                  className="site-btn site-btn-ghost whitespace-nowrap px-4 py-2 text-sm"
                >
                  {saving ? "Saving…" : "Save key"}
                </button>
              </div>
            </div>

            {(!composioUrls || Object.values(composioUrls).every(v => String(v).startsWith("error"))) ? (
              <button
                onClick={loadComposioUrls}
                disabled={composioLoading}
                className="site-btn site-btn-primary self-start px-6"
              >
                {composioLoading ? "Loading OAuth links…" : composioUrls ? "Retry loading links →" : "Load OAuth links →"}
              </button>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
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
                          ? "border-[var(--line)] bg-[rgba(246,246,248,0.03)] opacity-40 cursor-not-allowed"
                          : "border-blue-900/60 bg-blue-950/20 hover:border-blue-700 hover:bg-blue-950/20"
                      }`}
                      onClick={isError ? (e) => e.preventDefault() : undefined}
                    >
                      <span className="text-xl">{app.icon}</span>
                      <div className="flex flex-col gap-0.5 min-w-0">
                        <p className="font-medium text-white text-sm">{app.label}</p>
                        <p className="text-[var(--fg-mute)] text-xs truncate">{app.desc}</p>
                      </div>
                      {!isError && (
                        <span className="ml-auto whitespace-nowrap text-xs text-blue-300">Connect →</span>
                      )}
                    </a>
                  );
                })}
              </div>
            )}

            {error && (
              <p className="rounded-2xl border border-red-900/70 bg-red-950/30 px-4 py-3 text-sm text-red-300">
                {error}
              </p>
            )}

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setStep((s) => s + 1)}
                className="site-btn site-btn-primary px-6"
              >
                Finish setup →
              </button>
              <button
                onClick={handleSkip}
                className="site-btn site-btn-ghost px-5 text-sm"
              >
                Skip for now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step: Done */}
      {currentStepId === "done" && (
        <div className="site-card p-5 sm:p-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
          <div className="flex flex-col gap-3">
            <span className="site-pill px-2 py-1 text-green-200">Complete</span>
            <h2 className="text-[clamp(30px,3vw,52px)] leading-[0.96]">Setup complete</h2>
            <p className="text-sm leading-6 text-[var(--fg-dim)]">
              Astra is ready. You can connect more services anytime by returning to this page.
            </p>
            <Link href="/" className="site-btn site-btn-primary self-start px-6">
              Launch a goal →
            </Link>
          </div>

          <div className="flex flex-col gap-4">
            {status && (
              <div className="grid gap-3 sm:grid-cols-3">
                {(
                  [
                    { key: "github", label: "GitHub", icon: "🐙" },
                    { key: "sendgrid", label: "SendGrid", icon: "✉️" },
                    { key: "vercel", label: "Vercel", icon: "▲" },
                    { key: "instagram", label: "Instagram", icon: "📸" },
                    { key: "tiktok", label: "TikTok", icon: "🎵" },
                    { key: "meta_ads", label: "Meta Ads", icon: "📢" },
                  ] as Array<{ key: keyof SetupStatus; label: string; icon: string }>
                ).map((svc) => {
                  const connected = status[svc.key];
                  return (
                    <div
                      key={svc.key}
                      className={`rounded-xl border p-4 flex flex-col gap-2 ${
                        connected ? "border-green-900/60 bg-green-950/20" : "border-[var(--line)] bg-[rgba(246,246,248,0.03)]"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xl">{svc.icon}</span>
                        <span className={`text-xs font-mono ${connected ? "text-green-400" : "text-[var(--fg-mute)]"}`}>
                          {connected ? "✓" : "–"}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-white">{svc.label}</p>
                    </div>
                  );
                })}
              </div>
            )}

            <button
              onClick={() => { setStep(1); setError(null); }}
              className="site-btn site-btn-ghost self-start px-5 text-sm"
            >
              Add more services
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
