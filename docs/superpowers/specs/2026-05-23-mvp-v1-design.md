# Astra MVP v1 — Shippable Beta Design

**Date:** 2026-05-23
**Project:** Astra — AI Founding Team (Gemini XPRIZE Hackathon 2026)
**Team:** 2 engineers
**Target:** Shippable beta — 3 real founders go from text → Delaware LLC filed + landing page live

---

## Overview

MVP v1 = shippable beta. 4 stages. Stages 2 and 3 run in parallel after Stage 1 spine is complete.

```
Stage 1: Spine          (both engineers, ~1 week)
         ↓
Stage 2: Agents         (Engineer 1, ~2 weeks) ─┐
Stage 3: Dashboard      (Engineer 2, ~2 weeks) ─┤  parallel
         ↓                                      ┘
Stage 4: Integration    (both engineers, ~1 week)
```

**Total:** ~5-6 weeks. Lands at Week 5-6 of the 90-day XPRIZE plan.

---

## Stage 1: Spine

**Both engineers. ~1 week.**

Goal: one working `/goal` → `/task` → `/result` loop with Legal Agent only.

### Backend (FastAPI)

- Single FastAPI app, async throughout
- `/goal`, `/approve`, `/reject`, `/ask`, `/status` endpoints wired per command protocol
- Orchestrator runs as background coroutine — never blocks API thread
- Orchestrator loop: parse goal (Gemini Flash) → build DAG → write tasks to Supabase → dispatch to Redis → poll results → update graph → synthesize `/complete`

### Supabase Schema (5 tables)

| Table | Purpose |
|-------|---------|
| `founders` | Auth, plan tier, credit balance |
| `goals` | One row per `/goal`, status, elapsed time |
| `tasks` | DAG nodes: agent, depends_on[], status, result, approval_required |
| `approvals` | Pending human decisions, approval_token, expires_at |
| `memory_documents` | Agent outputs: doc_id, founder_id, namespace, agent, task_id, doc_type, content, summary, created_at, metadata, embedding |

### Redis (Upstash)

- `tasks:{founder_id}` — Orchestrator pushes tasks, agents pop
- `results:{founder_id}` — agents push results, Orchestrator polls

### AstraAgent Base Class

One class. All 6 agents are instantiations with different system_prompt/model/tools/memory_namespaces.

```python
class AstraAgent:
    def run(self, task: Task) -> AgentResult:
        memory = self.vector_db.retrieve(task.founder_id, self.memory_namespaces, task.instruction, k=5)
        messages = [system_prompt, build_prompt(task, memory)]
        raw = self._call_with_fallback(messages)
        parsed = json.loads(raw)
        # routes to: _request_approval / _report_blocked / _execute_and_return
```

Model call: OpenAI client pointed at `http://localhost:8080/v1` (llama.cpp + Gemma4 Q4_K_M for testing). Swap to Fireworks.ai before demo.

### Vector Memory

- Vertex AI initialized (text-embedding-004, free tier)
- **Write rule:** Orchestrator writes all `/result` outputs — agents never write directly
- Read: `retrieve_context(founder_id, namespace, query, k=5)`
- Namespaces: shared, legal, research, web, marketing, technical, ops

### Only Agent in Stage 1

Legal Agent (Gemma4 via llama.cpp for testing, Qwen3-30B-A3B via Fireworks in production).

### Gate

`/goal 'draft a founder agreement'` returns a real document via Legal Agent.

---

## Stage 2: All 6 Agents + Orchestrator Hardening

**Engineer 1. ~2 weeks. Parallel with Stage 3.**

### Add Agents 2-6

Same AstraAgent base class, new system_prompt/model/tools per instantiation:

| Agent | Model | Key Tools |
|-------|-------|-----------|
| Research | Qwen3-30B-A3B (Fireworks) + Gemini Search | gemini_search_grounding, report_generator |
| Web | Qwen3-30B-A3B (Fireworks) | framer_api, vercel_api |
| Marketing | Qwen3-30B-A3B (Fireworks) | email_sender (Resend), antigravity_computer_use |
| Technical | Qwen2.5-Coder-32B (Fireworks) | github_api, vercel_api, code_executor |
| Ops | Qwen3-30B-A3B (Fireworks) | reads all namespaces, 128k context |

### DAG Dependency Graph

```
Phase 1 (parallel):  research, legal
Phase 2 (parallel):  web (needs research), marketing (needs research)
Phase 3:             technical (needs web)
Phase 4 (always-on): ops (depends on all)
```

### Hardening

- **Fallback chain per agent:** primary model → Llama 3.1 70B (Fireworks) → Gemini 1.5 Flash (GCP)
- **Cost monitor:** log `{agent, model, input_tokens, output_tokens, cost_usd}` per call to Supabase. Hard cap: $2/day per founder. Above cap → queue for next day.
- **Replan on `/blocked`:** send blocked task + reason to Gemini Flash → returns reroute / split / escalate
- **Approval rules:**

| Action | Mode |
|--------|------|
| File LLC (with $500 charge) | Manual — always |
| Send cold email to 100+ contacts | Manual |
| Deploy landing page live | Manual |
| Update website headline | Manual |
| Generate draft legal document | Auto + notify |
| Post social media update | Auto + notify |
| Run market research report | Auto |

### Gate

`/goal 'launch my company'` runs all 6 agents end-to-end without crashing.

---

## Stage 3: Founder Dashboard

**Engineer 2. ~2 weeks. Parallel with Stage 2.**

Next.js + Vercel. Supabase Auth. Stripe payments.

### 6 Dashboard Panels

**Agent Status Ring**
- Visual ring per agent: Running / Waiting for Approval / Completed / Idle
- Real-time updates via WebSocket `/update` events from Orchestrator
- Click ring → open full activity log

**Approval Queue**
- Prioritized inbox of pending approvals
- Card shows: what agent did, recommended action, consequence
- Actions: Approve (1-click) / Reject (with reason) / Edit then approve
- Agent resumes immediately on approve

**Agent Chat Interface**
- One chat window per agent
- Sends `/ask` command to Orchestrator
- Response includes full company memory context
- Examples: "Legal Agent — draft an NDA", "Research Agent — competitor just launched"

**Company Timeline**
- Chronological feed of every agent action
- Filter by agent / date / task type
- Download any output (doc, report, code) directly

**Credit Balance & Usage**
- Current balance, monthly usage by agent, burn rate projection
- Inline Stripe credit purchase
- Per-agent credit limit controls

**Weekly Digest Preview**
- Ops Agent summary: what happened, what worked, what needs attention, priorities
- Approve and send to co-founders, or request revision before sending

### Auth & Payments

- Auth: Supabase Auth — `founder_id` scoped across all tables
- Payments: Stripe — Launch $249 one-time, Build $79/mo, Scale $149/mo, credits $10 each

### WebSocket

Orchestrator streams `/update` and `/complete` events → dashboard updates real-time.

Engineer 2 stubs WebSocket with mock events while Orchestrator is being built in Stage 2. Stubs replaced in Stage 4.

### Gate

Founder logs in, sees approval queue card, chats with agent, approves action.

---

## Stage 4: Integration + Shippable Beta

**Both engineers. ~1 week.**

### Integration

- Replace frontend WebSocket stubs with real Orchestrator events
- End-to-end smoke test: every dashboard panel reflects real agent activity
- Full approval flow: every agent output hits approval queue before executing

### Onboarding Flow

1. Founder types plain-English idea in text box
2. Gemini Flash extracts structured context (company name, ICP, problem, pricing hypotheses)
3. Context distributed to all agents simultaneously
4. Legal Agent starts within 24h
5. Landing page live within 48h

### Computer Use — Legal Agent (highest-risk piece)

Antigravity agent executes LLC filing on Stripe Atlas:

1. Approval gate (founder approves $500 charge — irreversible)
2. Antigravity session → `https://atlas.stripe.com/register`
3. Fill fields: company name, type, member name, email, ownership
4. Screenshot verification at each step via Qwen3
5. Second approval gate before payment click
6. Submit → capture confirmation number → screenshot to vector memory
7. IRS EIN flow (separate Antigravity session, same pattern)

**Fallback:** Harvard Business Services REST API (`$189` vs `$500` Stripe Atlas) if Antigravity fails.

### Legal Disclaimer

All generated documents must include:
> "AI-generated document preparation — not legal advice. Review with a licensed attorney before signing."

Never use the phrase "legal advice" anywhere in the product.

### Beta Readiness Checklist

- [ ] Per-founder $2/day compute cap enforced at infrastructure layer
- [ ] Legal disclaimer on all document outputs (attorney-reviewed copy)
- [ ] 3 real beta founders through full stack end-to-end
- [ ] Approval queue tested: LLC filing blocked until founder approves
- [ ] Stripe payments live and tested

### Gate

3 real beta founders: text description → Delaware LLC filed (real confirmation number) + live landing page (real URL). Show the receipts.

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python), async |
| Task store | Supabase (Postgres + Auth) |
| Message bus | Redis pub/sub (Upstash free tier) |
| Vector memory | Vertex AI — text-embedding-004 |
| Orchestrator AI | Gemini Flash (GCP — required XPRIZE touchpoint) |
| Agent models (prod) | Qwen3-30B-A3B + Qwen2.5-Coder-32B via Fireworks.ai |
| Agent models (test) | Gemma4 26B Q4_K_M via llama.cpp (`localhost:8080/v1`) |
| Computer Use | Antigravity (GCP, free as XPRIZE participant) |
| Search grounding | Gemini Search (GCP) |
| Frontend | Next.js + Vercel |
| Auth | Supabase Auth |
| Email | Resend (3k/mo free) |
| Web deploy | Framer API (primary) / Vercel API (fallback) |
| LLC fallback | Harvard Business Services REST API |
| Payments | Stripe |

---

## Risk Register (MVP-relevant)

| Risk | Level | Mitigation |
|------|-------|-----------|
| Gemma4 quality insufficient for testing | HIGH | Run evals on legal doc generation before building agents on top. Fall back to Fireworks early if needed. |
| Stripe Atlas Computer Use breaks | HIGH | HBS REST API fallback built in Stage 4. Don't block beta on Computer Use perfection. |
| Stage 2/3 integration surprises | MED | API contract (command protocol) defined in Eng Spec — both engineers build against same JSON schemas. |
| Too broad — agents shallow | HIGH | Stage 2 gate requires end-to-end without crashing, not quality. Quality hardened in post-beta. |
| Legal liability | HIGH | Disclaimer on all docs before any beta founder touches the product. |
