const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Task {
  id: string;
  goal_id: string;
  agent: string;
  status: "pending" | "running" | "done" | "blocked" | "awaiting_approval";
  output: Record<string, unknown> | null;
  reasoning: string | null;
  blocked_reason: string | null;
  depends_on: string[];
  created_at: string;
  updated_at: string;
}

export interface Goal {
  id: string;
  founder_id: string;
  raw_instruction: string;
  status: "running" | "done" | "blocked";
  created_at: string;
}

export interface GoalStatus {
  goal: Goal;
  tasks: Task[];
}

export interface AgentStackTemplate {
  stack_id: string;
  name: string;
  target_user: string;
  primary_outcome: string;
  description: string;
  input_prompts: string[];
  tasks: Array<{
    id: string;
    agent: string;
    title: string;
    instruction: string;
    depends_on: string[];
    artifacts: string[];
  }>;
  artifacts: Array<{
    key: string;
    title: string;
    owner_agent: string;
    description: string;
    required: boolean;
  }>;
  approval_gates: Array<{
    key: string;
    title: string;
    trigger: string;
    required_before: string;
    reason: string;
  }>;
  connector_requirements: Array<{
    key: string;
    label: string;
    category: string;
    purpose: string;
    required: boolean;
  }>;
  dashboard_sections: string[];
  completion_rules: string[];
}

export interface StackRecommendation {
  stack: AgentStackTemplate;
  confidence: number;
  reason: string;
  matched_signals: string[];
}

export interface StackReadiness {
  founder_id: string;
  stack_id: string;
  stack_name: string;
  ready: boolean;
  readiness_score: number;
  required_total: number;
  connected_required: number;
  missing_required: number;
  connectors: Array<{
    key: string;
    label: string;
    category: string;
    purpose: string;
    required: boolean;
    connected: boolean;
    source: string | null;
    status: "connected" | "missing_required" | "optional";
  }>;
  next_actions: string[];
}

export interface ConnectorCoverage {
  founder_id: string;
  stack_id: string;
  stack_name: string;
  required_total: number;
  ready_required: number;
  missing_required: number;
  connected_required_without_memory: number;
  coverage_score: number;
  summary: string;
  next_actions: string[];
  connectors: Array<StackReadiness["connectors"][number] & {
    brain_sources: Array<{ key: string; label: string; status: string; record_count: number }>;
    brain_record_count: number;
    brain_covered: boolean;
    coverage_status: "ready" | "connected_no_memory" | "memory_only" | "missing_required" | "optional_missing";
  }>;
}

export interface StackOperatingPlan {
  stack_id: string;
  stack_name: string;
  company_name: string;
  goal: string;
  outcome: string;
  operator_contract: string;
  phases: Array<{
    name: string;
    objective: string;
    lanes: Array<{ lane_id: string; agent: string; title: string }>;
  }>;
  lanes: Array<{
    id: string;
    agent: string;
    title: string;
    mission: string;
    depends_on: string[];
    artifact_keys: string[];
    artifacts: Array<{ key: string; title: string; description: string; required: boolean }>;
    handoff: string;
  }>;
  connector_plan: {
    required: Array<{ key: string; label: string; category: string; purpose: string }>;
    optional: Array<{ key: string; label: string; category: string; purpose: string }>;
    setup_rule: string;
  };
  approval_policy: Array<{
    key: string;
    title: string;
    trigger: string;
    required_before: string;
    reason: string;
  }>;
  artifact_contract: Array<{
    key: string;
    title: string;
    owner_agent: string;
    description: string;
    required: boolean;
    acceptance: string;
  }>;
  cadence: Record<string, string>;
  completion_definition: string[];
}

export interface AgentDepartmentManifest {
  stack_id: string;
  stack_name: string;
  company_name: string;
  goal: string;
  department_name: string;
  positioning: string;
  target_user: string;
  primary_outcome: string;
  workflow: {
    nodes: Array<{
      id: string;
      agent: string;
      title: string;
      mission: string;
      expected_outputs: Array<{ key: string; title: string; required: boolean }>;
      depends_on: string[];
    }>;
    edges: Array<{ from: string; to: string; handoff: string }>;
    critical_path: string[];
  };
  connectors: {
    required: Array<{ key: string; label: string; category: string; purpose: string; required: boolean }>;
    optional: Array<{ key: string; label: string; category: string; purpose: string; required: boolean }>;
    rule: string;
  };
  dashboards: Array<{ key: string; title: string; purpose: string }>;
  approvals: Array<{ key: string; title: string; trigger: string; required_before: string; founder_control: string }>;
  outputs: Array<{ key: string; title: string; owner_agent: string; description: string; required: boolean; acceptance: string }>;
  human_collaboration: {
    founder_role: string[];
    agent_role: string[];
    default_mode: string;
  };
  memory_policy: {
    canonical_records: string[];
    retrieval_promises: string[];
  };
  operating_plan: StackOperatingPlan;
}

export interface SessionDigest {
  session_id: string;
  company_name: string;
  stack_name: string;
  summary: string;
  counts: {
    planned_agents: number;
    done_agents: number;
    running_agents: number;
    ready_artifacts: number;
    outcome_events: number;
    outcome_units: number;
    triggered_approvals: number;
    pending_approvals: number;
    saferun_actions: number;
    errors: number;
  };
  done_agents: string[];
  running_agents: string[];
  ready_artifacts: Array<{ title?: string; owner_agent?: string; preview?: string }>;
  recent_outcomes: Array<{ label?: string; value?: number; unit?: string; preview?: string }>;
  approval_focus: Array<{ title?: string; status?: string; reason?: string }>;
  errors: string[];
  next_actions: string[];
}

export interface SubteamReport {
  session_id: string;
  team: string;
  agents: string[];
  summary: string;
  completed: Array<{ agent: string; summary: string }>;
  active: Array<{ agent: string; instruction: string }>;
  pending: Array<{ agent: string; instruction: string }>;
  artifacts: Array<{ title?: string; owner_agent?: string; preview?: string }>;
  outcomes: Array<{ label?: string; value?: number; unit?: string; preview?: string }>;
  approvals: Array<{ tool?: string; approval_gate?: string; reason?: string }>;
  blockers: string[];
  next_actions: string[];
}

export interface SessionAnswer {
  session_id: string;
  question: string;
  answer_type: "subteam_report" | "run_digest" | "stack_operating_plan" | "department_manifest" | "workboard";
  answer: string;
  confidence: number;
  report?: SubteamReport;
  digest?: SessionDigest;
  operating_plan?: StackOperatingPlan;
  manifest?: AgentDepartmentManifest;
  workboard?: SessionWorkboard;
}

export interface SessionWorkboard {
  session_id: string;
  stack_name: string;
  outcome: string;
  summary: string;
  counts: {
    total: number;
    queued: number;
    running: number;
    done: number;
    blocked: number;
    founder_next: number;
    agent_next: number;
  };
  pending_approvals: Array<Record<string, unknown>>;
  items: Array<{
    id: string;
    agent: string;
    owner_type: string;
    owner: string;
    title: string;
    mission: string;
    status: string;
    next_actor: "founder" | "founder_review" | "agent";
    depends_on: string[];
    expected_artifacts: Array<Record<string, unknown>>;
    ready_artifacts: Array<Record<string, unknown>>;
    outcomes: Array<Record<string, unknown>>;
    blockers: string[];
    summary: string;
  }>;
}

export interface SessionStateSnapshot {
  session_id: string;
  status: "running" | "done" | "error";
  event_count: number;
  last_event_id: number;
  stack?: AgentStackTemplate | null;
  operating_plan?: StackOperatingPlan | null;
  manifest?: AgentDepartmentManifest | null;
  company_genome?: Record<string, unknown> | null;
  digest?: SessionDigest | null;
  workboard?: SessionWorkboard | null;
  approvals: Array<Record<string, unknown>>;
  artifacts: Array<Record<string, unknown>>;
  outcomes: Array<Record<string, unknown>>;
  saferun_actions: Array<Record<string, unknown>>;
}

export interface SetupStatus {
  github: boolean;
  vercel: boolean;
  sendgrid: boolean;
  supabase: boolean;
  instagram: boolean;
  tiktok: boolean;
  meta_ads: boolean;
}

export interface SetupResult {
  founder_id: string;
  email: string;
  services: Record<string, unknown>;
  summary: string[];
  composio_oauth_urls?: Record<string, string>;
}

export interface BrainSource {
  key: string;
  label: string;
  kind: string;
  status: string;
  record_count: number;
  last_synced_at: string | null;
  notes: string;
  credential_fields?: string[];
  oauth_apps?: string[];
  setup_url?: string;
  setup_hint?: string;
  importer?: boolean;
}

export interface BrainRecord {
  id: string;
  source: string;
  kind: string;
  title: string;
  url: string;
  content: string;
  snippet?: string;
  canonical: boolean;
  stale_risk: string;
  status?: string;
  domain?: string;
  supersedes?: string[];
  updated_at: string;
  metadata?: Record<string, unknown>;
  score?: number;
}

export interface BrainRelationship {
  from: string;
  to: string;
  type: string;
  strength: number;
  evidence: string[];
}

export interface BrainProposal {
  id: string;
  kind: string;
  title: string;
  status: "open" | "resolved" | "dismissed";
  record_ids: string[];
  reason: string;
  suggested_update: string;
  created_at: string;
  updated_at?: string;
}

export interface BrainMaintenance {
  last_checked_at: string | null;
  stale_count: number;
  contradiction_count: number;
  missing_canonical_count: number;
}

export interface BrainSyncState {
  enabled: boolean;
  interval_minutes: number;
  sources: string[];
  last_run_at: string | null;
  next_run_at: string | null;
  last_status: string;
  last_error: string;
  history: Array<Record<string, unknown>>;
}

export interface BrainSchedulerState {
  running: boolean;
  interval_seconds: number;
  last_tick_at: string | null;
  last_result: Record<string, unknown> | null;
  last_error: string;
}

export interface BrainAnswerCitation {
  index: number;
  record_id: string;
  title: string;
  source: string;
  url?: string;
  canonical: boolean;
  score: number;
}

export interface CompanyBrain {
  founder_id: string;
  updated_at: string;
  sources: Record<string, BrainSource>;
  records: BrainRecord[];
  relationships: BrainRelationship[];
  proposals: BrainProposal[];
  maintenance: BrainMaintenance;
  sync: BrainSyncState;
}

export interface CompanySubteamReport {
  founder_id: string;
  team: string;
  agents: string[];
  window_days: number;
  record_count: number;
  session_count: number;
  by_kind: Record<string, number>;
  by_source: Record<string, number>;
  summary: string;
  highlights: Array<{
    id?: string;
    title?: string;
    source?: string;
    kind?: string;
    updated_at?: string;
    snippet?: string;
    canonical?: boolean;
  }>;
  next_actions: string[];
}

export async function submitGoal(
  founderId: string,
  instruction: string,
  constraints: Record<string, unknown> = {},
  stackId = "idea_to_revenue"
): Promise<{ session_id: string; status: string }> {
  const res = await fetch(`${BASE}/goal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ founder_id: founderId, instruction, constraints, stack_id: stackId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getStacks(): Promise<AgentStackTemplate[]> {
  const res = await fetch(`${BASE}/stacks`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.stacks ?? [];
}

export async function recommendStack(instruction: string, companyStage?: string): Promise<StackRecommendation> {
  const res = await fetch(`${BASE}/stacks/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ instruction, company_stage: companyStage }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getStackReadiness(founderId: string, stackId: string): Promise<StackReadiness> {
  const res = await fetch(`${BASE}/stacks/${encodeURIComponent(stackId)}/readiness/${encodeURIComponent(founderId)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getConnectorCoverage(founderId: string, stackId: string): Promise<ConnectorCoverage> {
  const res = await fetch(`${BASE}/stacks/${encodeURIComponent(stackId)}/connector-coverage/${encodeURIComponent(founderId)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getStackOperatingPlan(stackId: string, goal = "", companyName = ""): Promise<StackOperatingPlan> {
  const params = new URLSearchParams();
  if (goal) params.set("goal", goal);
  if (companyName) params.set("company_name", companyName);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${BASE}/stacks/${encodeURIComponent(stackId)}/operating-plan${suffix}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getStackManifest(stackId: string, goal = "", companyName = ""): Promise<AgentDepartmentManifest> {
  const params = new URLSearchParams();
  if (goal) params.set("goal", goal);
  if (companyName) params.set("company_name", companyName);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${BASE}/stacks/${encodeURIComponent(stackId)}/manifest${suffix}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function streamGoal(sessionId: string): EventSource {
  return new EventSource(`${BASE}/stream/${sessionId}`);
}

export async function getSessionDigest(sessionId: string): Promise<SessionDigest> {
  const res = await fetch(`${BASE}/sessions/${encodeURIComponent(sessionId)}/digest`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getSubteamReport(sessionId: string, team = "engineering"): Promise<SubteamReport> {
  const res = await fetch(`${BASE}/sessions/${encodeURIComponent(sessionId)}/subteam-report?team=${encodeURIComponent(team)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getSessionWorkboard(sessionId: string): Promise<SessionWorkboard> {
  const res = await fetch(`${BASE}/sessions/${encodeURIComponent(sessionId)}/workboard`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getSessionState(sessionId: string): Promise<SessionStateSnapshot> {
  const res = await fetch(`${BASE}/sessions/${encodeURIComponent(sessionId)}/state`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function askSession(sessionId: string, question: string, founderId?: string): Promise<SessionAnswer> {
  const res = await fetch(`${BASE}/sessions/${encodeURIComponent(sessionId)}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, founder_id: founderId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function continueSession(
  founderId: string,
  priorSessionId: string,
  instruction: string,
  agents?: string[]
): Promise<{ session_id: string; status: string; prior_session_id: string }> {
  const res = await fetch(`${BASE}/goal/continue`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ founder_id: founderId, prior_session_id: priorSessionId, instruction, agents }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getGoalStatus(goalId: string): Promise<GoalStatus> {
  const res = await fetch(`${BASE}/status/${goalId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function approveTask(taskId: string): Promise<void> {
  const res = await fetch(`${BASE}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_id: taskId, approval_token: "founder" }),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function rejectTask(taskId: string, reason: string): Promise<void> {
  const res = await fetch(`${BASE}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_id: taskId, reason }),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function decideStackApproval(
  sessionId: string,
  gateKey: string,
  decision: "approved" | "skipped",
  founderId?: string,
  note?: string
): Promise<void> {
  const res = await fetch(`${BASE}/stack/approval`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, gate_key: gateKey, decision, founder_id: founderId, note }),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function setupAccounts(
  founderId: string,
  email: string,
  password: string
): Promise<SetupResult> {
  const res = await fetch(`${BASE}/setup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ founder_id: founderId, email, password }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getSetupStatus(founderId: string): Promise<SetupStatus> {
  const res = await fetch(`${BASE}/setup/${founderId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function saveServiceCredential(
  founderId: string,
  service: string,
  credentials: Record<string, string>
): Promise<void> {
  const res = await fetch(`${BASE}/setup/service`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ founder_id: founderId, service, credentials }),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function getComposioOAuthUrls(
  founderId: string
): Promise<Record<string, string>> {
  const res = await fetch(`${BASE}/setup/composio/connect/${founderId}`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.oauth_urls ?? {};
}

export async function getCompanyBrain(founderId: string): Promise<CompanyBrain> {
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function syncCompanyBrain(
  founderId: string,
  sources?: string[]
): Promise<{ ok: boolean; record_count: number; relationship_count: number; changed_records: number; sources: BrainSource[] }> {
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sources }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function importCompanyBrainSources(
  founderId: string,
  sources?: string[],
  limit = 20
): Promise<{ ok: boolean; founder_id: string; results: Array<{ ok: boolean; source: string; error?: string; ingested?: number; changed_records?: number }>; imported_sources: string[]; failed_sources: string[] }> {
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sources, limit }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCompanyBrainAgentContext(
  founderId: string,
  query: string,
  limit = 8
): Promise<{ ok: boolean; context: string; records: BrainRecord[]; relationships: BrainRelationship[]; canonical_sources: BrainRecord[]; open_proposals: BrainProposal[]; sync: BrainSyncState }> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/agent-context?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function askCompanyBrain(
  founderId: string,
  question: string,
  limit = 8
): Promise<{ ok: boolean; question: string; answer: string; confidence: number; citations: BrainAnswerCitation[]; evidence: string[]; context: string }> {
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, limit }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCompanySubteamReport(founderId: string, team = "engineering", days = 7): Promise<CompanySubteamReport> {
  const params = new URLSearchParams({ team, days: String(days) });
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/subteam-report?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function configureCompanyBrainSync(
  founderId: string,
  config: { enabled: boolean; sources?: string[]; interval_minutes?: number }
): Promise<{ ok: boolean; sync: BrainSyncState }> {
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/sync/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runCompanyBrainSync(
  founderId: string,
  sources?: string[]
): Promise<{ ok: boolean; skipped: boolean; sync: BrainSyncState }> {
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/sync/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sources }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCompanyBrainSchedulerStatus(): Promise<{ ok: boolean; scheduler: BrainSchedulerState }> {
  const res = await fetch(`${BASE}/brain/scheduler/status`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function searchCompanyBrain(
  founderId: string,
  query: string,
  limit = 8
): Promise<{ query: string; count: number; results: BrainRecord[]; formatted: string }> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/search?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function addCompanyBrainRecord(
  founderId: string,
  record: { source: string; title: string; content: string; kind?: string; url?: string; canonical?: boolean; stale_risk?: string }
): Promise<{ ok: boolean; record: BrainRecord }> {
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/records`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(record),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function ingestCompanyBrainRecords(
  founderId: string,
  source: string,
  records: Array<Record<string, unknown>>
): Promise<{ ok: boolean; source: string; ingested: number; changed_records: number; record_count: number; proposal_count: number }> {
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source, records }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function maintainCompanyBrain(
  founderId: string
): Promise<{ ok: boolean; maintenance: BrainMaintenance; proposals: BrainProposal[] }> {
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/maintain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateBrainProposal(
  founderId: string,
  proposalId: string,
  status: "open" | "resolved" | "dismissed"
): Promise<{ ok: boolean; proposal?: BrainProposal; error?: string }> {
  const res = await fetch(`${BASE}/brain/${encodeURIComponent(founderId)}/proposals/${encodeURIComponent(proposalId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const AGENT_LABELS: Record<string, string> = {
  research: "Market Research",
  research_competitors: "Competitor Intel",
  research_execution: "Execution Strategy",
  web: "Web & Landing Page",
  marketing: "Marketing & Social",
  technical: "Technical Architecture",
  legal: "Legal & Compliance",
  ops: "Ops & Fundraising",
  sales: "Sales & Outreach",
  design: "Design & Brand",
};

export const AGENT_ORDER = ["research", "research_competitors", "research_execution", "web", "marketing", "technical", "legal", "ops", "sales", "design"];

const AGENT_ORDER_INDEX = new Map(AGENT_ORDER.map((agent, index) => [agent, index]));

export function sortAgentsByOrder<T extends { agent: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const aIndex = AGENT_ORDER_INDEX.get(a.agent) ?? Number.MAX_SAFE_INTEGER;
    const bIndex = AGENT_ORDER_INDEX.get(b.agent) ?? Number.MAX_SAFE_INTEGER;
    if (aIndex !== bIndex) return aIndex - bIndex;
    return a.agent.localeCompare(b.agent);
  });
}

export function sortAgentNamesByOrder(agentNames: string[]): string[] {
  return [...new Set(agentNames)].sort((a, b) => {
    const aIndex = AGENT_ORDER_INDEX.get(a) ?? Number.MAX_SAFE_INTEGER;
    const bIndex = AGENT_ORDER_INDEX.get(b) ?? Number.MAX_SAFE_INTEGER;
    if (aIndex !== bIndex) return aIndex - bIndex;
    return a.localeCompare(b);
  });
}

export const TOOL_DESCRIPTIONS: Record<string, string> = {
  github_create_repo: "Creating GitHub repository",
  supabase_create_project: "Provisioning Supabase database",
  supabase_generate_schema: "Designing database schema",
  clerk_generate_integration: "Setting up authentication",
  posthog_generate_integration: "Configuring analytics",
  clarity_setup_for_app: "Adding session recording",
  claude_code_scaffold: "Building codebase with Claude Code",
  vercel_deploy_from_github: "Deploying to Vercel",
  vercel_deploy: "Deploying to Vercel",
  cloudflare_setup_vercel_domain: "Configuring Cloudflare DNS",
  generate_landing_page_html: "Generating landing page",
  deep_research: "Deep research via Gemini + Google Search",
  web_search: "Searching the web",
  search_and_read: "Searching and reading pages",
  news_search: "Searching recent news",
  obsidian_log: "Saving session notes",
  generate_pdf: "Generating PDF document",
  send_email_campaign: "Sending email campaign",
  composio_gmail_send: "Sending email",
  composio_linear_create_issue: "Creating Linear tickets",
  composio_notion_create_page: "Writing to Notion",
  resend_send_email: "Sending email via Resend",
  find_leads: "Finding leads",
  enrich_lead: "Enriching lead data",
  build_outreach_sequence: "Building outreach sequence",
  format_legal_document: "Drafting legal document",
  generate_wireframe: "Generating wireframe",
  generate_color_palette: "Generating color palette",
};
