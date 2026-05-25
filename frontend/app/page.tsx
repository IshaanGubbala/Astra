"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitGoal } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [instruction, setInstruction] = useState("");
  const [founderId, setFounderId] = useState("founder_001");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!instruction.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await submitGoal(founderId, instruction);
      router.push(`/goal/${result.session_id}?instruction=${encodeURIComponent(instruction)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit goal");
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-16">
      <section className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <div className="flex flex-col gap-7">
          <div className="flex flex-col gap-4">
            <div className="eyebrow">Astra · AI founding team</div>
            <h1>
              You bring the idea.
              <br />
              <span className="display-italic">Astra does the rest.</span>
            </h1>
            <p className="lede">
              Describe the company you want to build. Astra coordinates research, product, legal, and growth work as a single operating system instead of a stack of disconnected tools.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { value: "6", label: "specialized agents" },
              { value: "72h", label: "to first launch pass" },
              { value: "1", label: "instruction to start" },
            ].map((stat) => (
              <div key={stat.label} className="site-card site-card-soft px-4 py-4">
                <div className="text-2xl text-white">{stat.value}</div>
                <div className="site-label mt-2">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="site-card p-5 sm:p-6">
          <div className="flex items-center justify-between gap-4 border-b border-[var(--line)] pb-4">
            <div>
              <p className="site-label">Launch prompt</p>
              <p className="mt-2 text-sm text-[var(--fg-dim)]">
                Give Astra the first instruction and it will start planning the full company.
              </p>
            </div>
            <span className="site-pill">Live</span>
          </div>

          <form onSubmit={handleSubmit} className="mt-5 flex flex-col gap-4">
            <textarea
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="Build a SaaS product for indie hackers to track MRR across Stripe, Lemon Squeezy, and Paddle, then launch a landing page and waitlist."
              rows={7}
              className="site-textarea resize-none px-4 py-4 text-base leading-6"
              disabled={loading}
            />

            <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
              <div className="flex flex-col gap-2">
                <label className="site-label">Founder ID</label>
                <input
                  value={founderId}
                  onChange={(e) => setFounderId(e.target.value)}
                  className="site-input px-4 py-3 text-sm text-white"
                  placeholder="founder_001"
                />
              </div>

              <button
                type="submit"
                disabled={loading || !instruction.trim()}
                className="site-btn site-btn-primary px-5"
              >
                {loading ? "Launching agents…" : "Launch Astra"}
                <span aria-hidden="true">→</span>
              </button>
            </div>

            {error && (
              <p className="rounded-2xl border border-red-900/70 bg-red-950/30 px-4 py-3 text-sm text-red-300">
                {error}
              </p>
            )}

            <div className="flex flex-wrap gap-3 pt-1">
              <Link href="/setup" className="site-btn site-btn-ghost">
                Connect accounts
              </Link>
              <Link href="/#process" className="site-btn site-btn-ghost">
                View process
              </Link>
            </div>
          </form>
        </div>
      </section>

      <div className="site-rule" />

      <section id="process" className="grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="flex flex-col gap-4">
          <div className="eyebrow">The flow</div>
          <h2>
            One instruction.
            <br />
            <span className="display-italic">A full founding stack.</span>
          </h2>
          <p className="lede">
            Astra turns a plain-English goal into a coordinated work plan across research, web, marketing, legal, technical, and operations.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {[
            { step: "01", title: "Research", desc: "Market sizing, competitors, and a recommendation before you spend a dollar." },
            { step: "02", title: "Build", desc: "Landing pages, product scaffolds, and deployment artifacts from one brief." },
            { step: "03", title: "Launch", desc: "Copy, campaigns, and distribution assets built around the same strategy." },
            { step: "04", title: "Operate", desc: "Weekly digests, task queues, and the recurring work that keeps the company moving." },
          ].map((item) => (
            <article key={item.step} className="site-card site-card-soft p-5">
              <div className="site-label">{item.step}</div>
              <h3 className="mt-3 text-[28px] leading-none">{item.title}</h3>
              <p className="mt-4 text-sm leading-6 text-[var(--fg-dim)]">{item.desc}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        {[
          { icon: "🔬", label: "Research", desc: "TAM, SAM, SOM, competitors, and customer profile work." },
          { icon: "🌐", label: "Web", desc: "Landing pages and app scaffolds that ship with your idea." },
          { icon: "📢", label: "Growth", desc: "Campaigns, social content, and outreach built from the same plan." },
          { icon: "⚙️", label: "Technical", desc: "Repository scaffolding, architecture, and implementation support." },
          { icon: "⚖️", label: "Legal", desc: "Entity setup, policies, and compliance-driven drafting." },
          { icon: "🚀", label: "Ops", desc: "Coordination, approvals, and a persistent memory of company decisions." },
        ].map((item) => (
          <div key={item.label} className="site-card site-card-soft p-5">
            <span className="text-2xl">{item.icon}</span>
            <p className="mt-4 text-sm font-medium tracking-wide text-white">{item.label}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--fg-dim)]">{item.desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
