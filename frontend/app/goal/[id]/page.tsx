"use client";

import { use, useEffect, useState, useCallback } from "react";
import {
  getGoalStatus,
  approveTask,
  rejectTask,
  GoalStatus,
  Task,
  AGENT_LABELS,
  AGENT_ORDER,
} from "@/lib/api";

const STATUS_COLOR: Record<string, string> = {
  pending: "text-zinc-500",
  running: "text-yellow-400",
  done: "text-green-400",
  blocked: "text-red-400",
  awaiting_approval: "text-violet-400",
};

const STATUS_DOT: Record<string, string> = {
  pending: "bg-zinc-600",
  running: "bg-yellow-400 animate-pulse",
  done: "bg-green-400",
  blocked: "bg-red-400",
  awaiting_approval: "bg-violet-400 animate-pulse",
};

function AgentCard({ task, onApprove, onReject }: {
  task: Task;
  onApprove: (id: string) => void;
  onReject: (id: string, reason: string) => void;
}) {
  const label = AGENT_LABELS[task.agent] ?? task.agent;
  const [rejecting, setRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${STATUS_DOT[task.status] ?? "bg-zinc-500"}`} />
          <h3 className="font-semibold text-zinc-200">{label}</h3>
        </div>
        <span className={`text-xs font-mono uppercase ${STATUS_COLOR[task.status] ?? "text-zinc-400"}`}>
          {task.status.replace("_", " ")}
        </span>
      </div>

      {task.status === "running" && (
        <p className="text-zinc-500 text-sm animate-pulse">Working…</p>
      )}

      {task.status === "done" && task.output && (
        <OutputView agent={task.agent} output={task.output} />
      )}

      {task.status === "blocked" && (
        <p className="text-red-400 text-sm">
          {task.blocked_reason ?? "Blocked — manual intervention required"}
        </p>
      )}

      {task.status === "awaiting_approval" && (
        <div className="flex flex-col gap-2">
          <p className="text-violet-300 text-sm">
            {(task.output?.approval_prompt as string | undefined) ?? "Approval required before proceeding"}
          </p>
          {!rejecting ? (
            <div className="flex gap-2">
              <button
                onClick={() => onApprove(task.id)}
                className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-500"
              >
                Approve
              </button>
              <button
                onClick={() => setRejecting(true)}
                className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:border-zinc-500"
              >
                Reject
              </button>
            </div>
          ) : (
            <div className="flex gap-2">
              <input
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Reason for rejection…"
                className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 focus:border-violet-500 focus:outline-none"
              />
              <button
                onClick={() => { onReject(task.id, rejectReason); setRejecting(false); }}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500"
              >
                Send
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function OutputView({ agent, output }: { agent: string; output: Record<string, unknown> }) {
  if (agent === "research") {
    return (
      <div className="flex flex-col gap-2 text-sm">
        {!!output.report_title && (
          <p className="font-semibold text-zinc-200">{String(output.report_title)}</p>
        )}
        <div className="grid grid-cols-3 gap-2">
          {["tam_usd", "sam_usd", "som_usd"].map((k) =>
            output[k] ? (
              <div key={k} className="rounded-lg bg-zinc-800 p-2 text-center">
                <p className="text-xs text-zinc-500 uppercase">{k.replace("_usd", "")}</p>
                <p className="text-green-400 font-mono text-sm">${Number(output[k]).toLocaleString()}</p>
              </div>
            ) : null
          )}
        </div>
        {!!output.key_insights && (
          <ul className="list-disc list-inside text-zinc-400 space-y-1">
            {(output.key_insights as string[]).slice(0, 4).map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  if (agent === "web") {
    return (
      <div className="flex flex-col gap-2 text-sm">
        {!!(output.deployed && output.site_url) && (
          <a
            href={String(output.site_url)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-violet-400 hover:underline font-mono"
          >
            {String(output.site_url)} ↗
          </a>
        )}
        {!output.deployed && (
          <p className="text-zinc-400">Landing page generated (deploy Vercel token required for live URL)</p>
        )}
      </div>
    );
  }

  if (agent === "marketing") {
    return (
      <div className="flex flex-col gap-2 text-sm text-zinc-400">
        {!!output.instagram_reel && <p>✓ Instagram Reel package ready</p>}
        {!!output.tiktok && <p>✓ TikTok script ready</p>}
        {!!output.meta_ad && <p>✓ Meta Ad spec ready</p>}
        {!!output.campaigns_launched && <p className="text-green-400">✓ Campaigns launched</p>}
      </div>
    );
  }

  if (agent === "technical") {
    return (
      <div className="flex flex-col gap-2 text-sm">
        {!!output.github_repo && (
          <a
            href={String(output.github_repo)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-violet-400 hover:underline font-mono"
          >
            {String(output.github_repo)} ↗
          </a>
        )}
        {!!output.tech_decisions && (
          <p className="text-zinc-400">{String(output.tech_decisions)}</p>
        )}
      </div>
    );
  }

  if (agent === "legal") {
    return (
      <div className="flex flex-col gap-2 text-sm text-zinc-400">
        {!!output.documents_drafted && (
          <p>✓ {String(output.documents_drafted)} document(s) drafted</p>
        )}
        {!!output.jurisdiction && <p>Jurisdiction: {String(output.jurisdiction)}</p>}
      </div>
    );
  }

  if (agent === "ops") {
    return (
      <div className="flex flex-col gap-2 text-sm text-zinc-400">
        {!!output.investor_opportunities && (
          <p>✓ {(output.investor_opportunities as unknown[]).length} investor opportunities found</p>
        )}
        {!!output.accelerators && (
          <p>✓ {(output.accelerators as unknown[]).length} accelerators identified</p>
        )}
      </div>
    );
  }

  return (
    <pre className="text-xs text-zinc-400 overflow-auto max-h-40 bg-zinc-950 rounded p-2">
      {JSON.stringify(output, null, 2)}
    </pre>
  );
}

export default function GoalPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [data, setData] = useState<GoalStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const poll = useCallback(async () => {
    try {
      const result = await getGoalStatus(id);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load status");
    }
  }, [id]);

  useEffect(() => {
    poll();
    const iv = setInterval(() => {
      if (data?.goal.status === "running" || !data) {
        poll();
      }
    }, 3000);
    return () => clearInterval(iv);
  }, [poll, data?.goal.status]);

  async function handleApprove(taskId: string) {
    await approveTask(taskId);
    poll();
  }

  async function handleReject(taskId: string, reason: string) {
    await rejectTask(taskId, reason);
    poll();
  }

  if (error) {
    return <p className="text-red-400">{error}</p>;
  }

  if (!data) {
    return (
      <div className="flex items-center gap-3 text-zinc-400">
        <span className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
        Loading goal…
      </div>
    );
  }

  const tasksByAgent = Object.fromEntries(data.tasks.map((t) => [t.agent, t]));
  const doneCount = data.tasks.filter((t) => t.status === "done").length;
  const total = data.tasks.length;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white truncate max-w-2xl">
            {data.goal.raw_instruction}
          </h1>
          <span className={`text-sm font-mono px-2 py-0.5 rounded border ${
            data.goal.status === "done"
              ? "text-green-400 border-green-800 bg-green-950/30"
              : "text-yellow-400 border-yellow-800 bg-yellow-950/30"
          }`}>
            {data.goal.status}
          </span>
        </div>
        <p className="text-zinc-500 text-sm font-mono">{id}</p>
        <div className="flex items-center gap-2 mt-1">
          <div className="flex-1 h-1.5 rounded-full bg-zinc-800">
            <div
              className="h-1.5 rounded-full bg-violet-500 transition-all duration-500"
              style={{ width: total > 0 ? `${(doneCount / total) * 100}%` : "0%" }}
            />
          </div>
          <span className="text-zinc-400 text-sm">{doneCount}/{total}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {AGENT_ORDER.map((agent) => {
          const task = tasksByAgent[agent];
          if (!task) return null;
          return (
            <AgentCard
              key={agent}
              task={task}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          );
        })}
      </div>
    </div>
  );
}
