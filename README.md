# Astra — AI Founding Team

Astra turns a single plain-English instruction into a coordinated company-building operation. Six specialized AI agents run in parallel — doing market research, drafting legal documents, deploying landing pages, scaffolding codebases, creating marketing content, and managing operations — without any further input from the founder.

Live at **http://167.235.151.204** (Clerk auth required).

---

## What It Does

Submit one goal. Astra plans, dispatches, and executes across six domains simultaneously:

| Agent | What It Produces |
|---|---|
| **Research** | Market sizing, competitor analysis, TAM/SAM/SOM, customer profile, data sources, YouTube competitor analysis |
| **Legal** | NDAs, privacy policies, terms of service, founder agreements — full PDFs with patent landscape |
| **Web** | Landing page designed (Qwen3.6-35B, 2-pass generation) and deployed to Vercel via CLI |
| **Marketing** | Instagram Reels scripts, TikTok content, Meta ad copy, email campaigns, outreach sequences |
| **Technical** | Full codebase scaffolded via Claude Code CLI, Linear tickets, Notion pages, GitHub repo |
| **Ops** | Executive summary, investor outreach emails, fundraising docs, SOPs |

Everything runs in under 15 minutes. Results are streamed live to the dashboard and logged to an Obsidian vault.

---

## Architecture

```
POST /goal
    │
    ▼
Orchestrator (planner LLM)
    │  Decomposes goal into agent tasks with dependency order
    ▼
Wave Scheduler (asyncio.gather)
    │
    ├── research agent ──────────────────────────────────┐
    │                                                    │
    ├── (waits for research) ──────────────────────────  │
    │       ├── web agent                                │
    │       ├── legal agent                              │  parallel
    │       ├── marketing agent                          │
    │       └── technical agent                          │
    │                                                    │
    └── ops agent (runs last, sees all results) ─────────┘
    │
    ▼
SSE stream → Next.js dashboard (live agent cards)
    │
    ▼
Obsidian vault (persistent session notes per agent)
```

Each agent is a hand-rolled agentic loop:
1. LLM receives system prompt + tool schemas
2. LLM outputs tool call
3. Tool executes, result appended to messages
4. Repeat until `done` called or iteration cap hit

No LangChain. No LlamaIndex. No Agents SDK. Raw OpenAI-compatible chat completions + tool dispatch.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.13, asyncio |
| Frontend | Next.js 16, Tailwind CSS v4, SSE streaming, Clerk auth |
| Agent LLM | DeepSeek-V4-Flash via DeepInfra |
| Planner LLM | Llama 4 Scout 17B via DeepInfra |
| HTML Gen | Qwen3.6-35B-A3B via DeepInfra (2-pass, ~44k chars) |
| Database | Supabase (PostgreSQL) |
| Cache / Bus | Redis (Upstash-compatible) |
| Memory | Obsidian vault at `~/agent-workspace/` |
| OAuth Tools | Composio (Gmail, LinkedIn, GitHub, Linear, Notion, Google Calendar) |
| Deploy | Vercel CLI (landing pages), GitHub (repos + scaffolding via Claude Code CLI) |
| Docs | ReportLab (PDF generation) |
| Search | DuckDuckGo (`ddgs`), YouTube Transcript API |
| Auth | Clerk (sign-in/sign-up, JWT, OAuth) |
| Infrastructure | Docker Compose on VPS, nginx reverse proxy |

---

## Agent Tools

**Research:** `web_search`, `news_search`, `patent_search`, `youtube_research`, `obsidian_log`

**Legal:** `format_legal_document`, `generate_pdf`, `patent_search`, `obsidian_log`

**Web:** `generate_landing_page_html`, `vercel_deploy`, `obsidian_log`

**Marketing:** `generate_reel_package`, `generate_tiktok_package`, `generate_meta_ad`, `send_email_campaign`, `outreach_find_leads`, `obsidian_log`

**Technical:** `github_create_repo`, `claude_code_scaffold`, `composio_linear_create_issue`, `composio_notion_create_page`, `obsidian_log`

**Ops:** `generate_pdf`, `send_email_campaign`, `composio_linear_create_issue`, `composio_notion_create_page`, `obsidian_log`

---

## Agent Stack Platform

Astra includes a production-grade **Agent Stack Platform** under `backend/stacks/`. Instead of ad-hoc agent runs, founders select a pre-built stack (or describe an outcome) and get a fully-compiled AI department package:

- **Idea to Revenue Stack** — research → legal → web → marketing → ops, end-to-end
- **Sales Stack** — lead gen, outreach, CRM sync, pipeline management
- **Marketing Stack** — GTM, content calendar, ad ops, analytics
- **Founder Ops Stack** — task management, investor updates, board prep
- **Customer Support Stack** — ticket routing, knowledge base, escalation
- **Product Stack** — spec writing, sprint planning, release notes

Each stack compiles into an execution blueprint with lanes, artifacts, connectors, approval gates, KPIs, and quality gates. All 6 stacks currently score 100/100 on the quality checker.

```
POST /stacks/package   — compile a stack from a business outcome
GET  /stacks           — list available stacks
GET  /ready            — full objective readiness check (all stacks + platform health)
GET  /metrics          — Prometheus metrics endpoint
```

---

## Company Brain

Astra includes a local-first company brain that normalizes context from GitHub, Slack, Notion, Google Drive, Gmail, Linear, Zendesk, Confluence, and Astra agent memory into one searchable graph. It tracks canonical records, stale/conflicting knowledge, source relationships, and continuous sync state.

Backend agents receive compact company-brain context automatically during goal runs. External coding agents and IDE clients can also access it through the stdio JSON-RPC bridge:

```bash
ASTRA_FOUNDER_ID=founder_001 python -m backend.tools.company_brain_mcp
```

Example MCP-style client config:

```json
{
  "mcpServers": {
    "astra-company-brain": {
      "command": "python",
      "args": ["-m", "backend.tools.company_brain_mcp"],
      "env": {
        "ASTRA_FOUNDER_ID": "founder_001"
      }
    }
  }
}
```

---

## Key Design Decisions

**One-shot tool guard** — Expensive tools (`format_legal_document`, `vercel_deploy`, `generate_landing_page_html`, `claude_code_scaffold`) are hard-blocked after first successful execution per session. Prevents the LLM from calling them twice and doubling cost/time.

**One-shot obsidian_read** — Each agent's `obsidian_read` fires exactly once per run. On repeat calls, returns a `_blocked` message forcing the agent forward. Prevents infinite read loops that eat all iterations.

**2-pass HTML generation** — Web agent generates a full landing page (~37k chars, ~3.5 min) then runs a targeted polish pass: fills sparse sections, adds IntersectionObserver animations, tightens spacing, deepens hero. Final output ~44k chars. Vercel deploys the cached version — LLM cannot truncate it.

**Iteration pressure** — After iteration 5, the agent receives a message nudging it toward `done`. Prevents infinite tool loops.

**Run ledger** — Every agent event is durably recorded to `.astra/run_ledger/index.json` (absolute path, CWD-safe). Tracks per-session status, agent counts, artifact counts, durations. Exposed via `/metrics`.

**Claude Code CLI scaffold** — Technical agent clones the GitHub repo, runs Claude Code non-interactively inside it, then commits and pushes. Produces 20-30 real files with working code, not stubs.

**Obsidian vault** — Each agent writes structured session notes. Prior notes are loaded before each new run, giving agents cross-session memory without a vector database.

**SafeRun approval gates** — High-risk actions (Vercel deploy, repo creation, email sends) require founder approval before executing. In test mode, `bypass_approvals=True` skips the gate. In production, the approval queue is durable and role-aware.

---

## Proprietary Intelligence Layer

Four compounding systems under `proprietary-agent/` that make Astra smarter with every run:

- **Causal Decision Graph** — NetworkX graph tracking every agent decision, its causes, and outcomes. Agents query it before acting. Becomes a queryable company brain over time.
- **Silent Observer** — 24/7 background agent monitoring competitor activity, regulatory changes, and industry signals. Surfaces proactive alerts without being asked.
- **Execution Fingerprinting** — Every run compressed into a fingerprint. New runs matched against history: "78% similar to a run that succeeded — here's what worked and what failed."
- **Founder Mirror** — Adversarial agent that attacks every specialist output before it ships. Returns pass/flag/block verdict. Forces outputs to survive scrutiny.

See `proprietary-agent/README.md` for full design.

---

## Setup

### Requirements

- Python 3.13+
- Node.js 20+
- Redis
- Supabase project
- Clerk application (for auth)

### Install

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### Environment

```bash
cp .env.example .env
```

Required variables:

```env
SUPABASE_URL=
SUPABASE_KEY=
REDIS_URL=redis://localhost:6379
AGENT_MODEL_BASE_URL=https://api.deepinfra.com/v1/openai
AGENT_MODEL_API_KEY=
AGENT_MODEL_NAME=deepseek-ai/DeepSeek-V4-Flash
PLANNER_MODEL_API_KEY=
COMPOSIO_API_KEY=
GITHUB_TOKEN=
VERCEL_TOKEN=
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
```

### Run (local)

```bash
# Backend (port 8000)
uvicorn backend.main:app --port 8000

# Frontend (port 3000)
cd frontend && npm run dev
```

### Run (Docker)

```bash
cp .env.example .env   # fill in values
docker compose up -d --build
```

Open `http://localhost:3000`, sign in, enter a goal, click Launch.

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/goal` | Submit a goal, returns `session_id` |
| `GET` | `/stream/{session_id}` | SSE stream of agent events |
| `GET` | `/status/{goal_id}` | Goal + task status |
| `GET` | `/health` | Service health check |
| `GET` | `/ready` | Full objective readiness check |
| `GET` | `/metrics` | Prometheus metrics |
| `POST` | `/stacks/package` | Compile a stack from a business outcome |
| `GET` | `/stacks` | List available stacks |
| `POST` | `/setup` | Provision GitHub/Vercel/SendGrid accounts |
| `GET` | `/setup/{founder_id}` | Check which services are connected |
| `GET` | `/setup/composio/connect/{founder_id}` | Get OAuth URLs for Composio apps |

### SSE Event Types

```
goal_start           — run acknowledged
plan_done            — planner finished, tasks list available
agent_start          — specialist began
agent_action         — tool call in progress
agent_action_result  — tool returned
agent_done           — specialist finished, result available
goal_done            — all agents complete
goal_error           — unrecoverable failure
```

---

## Project Structure

```
Astra/
├── backend/
│   ├── core/
│   │   ├── agent.py           # Agentic loop — LLM + tool dispatch
│   │   ├── orchestrator.py    # Planner + wave scheduler
│   │   ├── factory.py         # Singleton orchestrator with all specialists
│   │   ├── events.py          # SSE pub/sub via Redis
│   │   └── bus.py             # Agent message bus
│   ├── specialists/
│   │   ├── research.py
│   │   ├── legal.py           # One-shot obsidian_read wrapper
│   │   ├── web.py             # One-shot obsidian_read + 2-pass HTML gen
│   │   ├── marketing.py
│   │   ├── technical.py
│   │   └── ops.py
│   ├── stacks/                # Agent Stack Platform
│   │   ├── compiler.py
│   │   ├── execution_blueprint.py
│   │   ├── execution_contracts.py
│   │   ├── manifest.py
│   │   ├── operating_plan.py
│   │   ├── package.py
│   │   ├── readiness.py
│   │   ├── template_quality.py
│   │   └── templates.py       # 6 production stack definitions
│   ├── tools/
│   │   ├── _llm.py            # Sync LLM wrapper
│   │   ├── vercel_deploy.py   # 2-pass HTML gen + Vercel CLI deploy
│   │   ├── claude_scaffold.py # Claude Code CLI repo scaffolding
│   │   ├── github_scaffold.py # GitHub repo creation
│   │   ├── doc_generator.py   # Legal document generation
│   │   ├── pdf_generator.py   # PDF rendering via ReportLab
│   │   ├── social_content.py  # Reels, TikTok, Meta ad copy
│   │   ├── email_campaign.py  # SendGrid email campaigns
│   │   ├── outreach.py        # Hunter-driven lead discovery + Gmail campaigns
│   │   ├── web_search.py      # Web + news search
│   │   ├── patent_search.py   # Patent search
│   │   ├── composio_tools.py  # OAuth tool execution via Composio
│   │   └── obsidian_logger.py # Vault read/write/append
│   ├── safety/
│   │   └── saferun.py         # Approval gates for high-risk actions
│   ├── run_ledger.py          # Durable per-run operational log
│   ├── platform_status.py     # Health/readiness/metrics
│   ├── api/
│   │   └── routes.py
│   └── config.py              # Pydantic settings from .env
├── frontend/
│   └── app/
│       ├── page.tsx            # Goal submission
│       ├── goal/[id]/page.tsx  # Live agent dashboard
│       ├── payments/page.tsx   # Billing + plans
│       └── setup/page.tsx      # Account connection
├── deploy/
│   ├── nginx.conf
│   ├── server-preflight.sh
│   └── production-proof.sh
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── supabase/                   # Schema migrations
└── tests/
```

---

## Cost

A full 6-agent run costs approximately **$0.03–0.08** in LLM tokens at current DeepInfra pricing. HTML generation (Qwen3.6-35B, 2 passes) adds ~$0.02. Claude Code scaffold (technical agent) uses Anthropic credits separately.

---

## License

Proprietary. All rights reserved.
