"""
Ruflo MCP Compatibility Bridge.

Exposes each Astra specialist as an MCP-compatible tool so they can run
inside Ruflo swarms, use Ruflo's AgentDB memory, and participate in
SONA self-learning trajectory tracking.

Architecture:
  - MCP tool manifest: each specialist = one MCP tool (agent_spawn interface)
  - RufloMemoryAdapter: wraps Obsidian vault calls into namespace-isolated AgentDB writes
  - SONATracker: feeds execution fingerprints into Ruflo's learning system
  - MCPToolBridge: discovers + routes calls to any external MCP server
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# MCP Tool Manifest
# ------------------------------------------------------------------ #

MCP_TOOL_MANIFEST = {
    "astra_research": {
        "name": "astra_research",
        "description": "Market research, TAM/SAM/SOM analysis, competitor intelligence, patent search. Returns structured JSON with market_size, competitors, customer_profile, data_sources.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "Research objective (e.g. 'market size for B2B dental SaaS')"},
                "founder_id": {"type": "string", "description": "Founder identifier for context isolation"},
                "session_id": {"type": "string", "description": "Session identifier for event streaming"},
                "domains": {"type": "array", "items": {"type": "string"}, "description": "Market domains to focus on"},
            },
            "required": ["goal", "founder_id"],
        },
    },
    "astra_legal": {
        "name": "astra_legal",
        "description": "Legal document drafting: NDAs, privacy policies, terms of service, founder agreements, IP assignment. Returns formatted legal text and optionally a PDF.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "founder_id": {"type": "string"},
                "session_id": {"type": "string"},
                "company_name": {"type": "string"},
                "doc_types": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["goal", "founder_id"],
        },
    },
    "astra_web": {
        "name": "astra_web",
        "description": "Landing page generation and Vercel deployment. Creates GitHub repo with production-ready HTML/CSS, deploys to Vercel. Returns live_url and repo_url.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "founder_id": {"type": "string"},
                "session_id": {"type": "string"},
                "company_name": {"type": "string"},
                "value_props": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["goal", "founder_id"],
        },
    },
    "astra_marketing": {
        "name": "astra_marketing",
        "description": "Social content creation: Instagram Reels scripts, TikTok packages, Meta ad copy, email campaigns. Returns structured content ready for publishing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "founder_id": {"type": "string"},
                "session_id": {"type": "string"},
                "target_platforms": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["goal", "founder_id"],
        },
    },
    "astra_technical": {
        "name": "astra_technical",
        "description": "Full codebase scaffolding via Claude Code CLI. Creates GitHub repo, runs Claude Code non-interactively, commits 20-30 production files. Returns repo_url and files_created.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "founder_id": {"type": "string"},
                "session_id": {"type": "string"},
                "tech_stack": {"type": "string"},
                "create_linear_tickets": {"type": "boolean"},
                "create_notion_page": {"type": "boolean"},
            },
            "required": ["goal", "founder_id"],
        },
    },
    "astra_ops": {
        "name": "astra_ops",
        "description": "Operations documents: executive summaries, investor outreach emails, fundraising docs, SOPs, board decks. Returns PDF paths and structured content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "founder_id": {"type": "string"},
                "session_id": {"type": "string"},
                "doc_types": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["goal", "founder_id"],
        },
    },
    "astra_mirror": {
        "name": "astra_mirror",
        "description": "Adversarial quality review. Attacks any agent output and returns pass/flag/block verdict with critique and questions. Use to gate outputs before delivery.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "enum": ["research", "legal", "web", "marketing", "technical", "ops"]},
                "output": {"type": "string", "description": "Full agent output to review"},
            },
            "required": ["agent", "output"],
        },
    },
    "astra_observer": {
        "name": "astra_observer",
        "description": "Proactive intelligence monitoring. Returns pending competitor/regulatory/funding alerts relevant to the founder's domains. Configured from the decision graph.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "founder_id": {"type": "string"},
                "domains": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["founder_id"],
        },
    },
}


@dataclass
class MCPToolCall:
    tool_name: str
    args: dict
    call_id: str = ""


@dataclass
class MCPToolResult:
    tool_name: str
    content: list[dict]
    is_error: bool = False

    @classmethod
    def success(cls, tool_name: str, data: Any) -> "MCPToolResult":
        return cls(
            tool_name=tool_name,
            content=[{"type": "text", "text": json.dumps(data, default=str)}],
        )

    @classmethod
    def error(cls, tool_name: str, message: str) -> "MCPToolResult":
        return cls(
            tool_name=tool_name,
            content=[{"type": "text", "text": f"Error: {message}"}],
            is_error=True,
        )


# ------------------------------------------------------------------ #
# MCP Server — exposes Astra agents as tools
# ------------------------------------------------------------------ #

class AstraMCPServer:
    """
    Minimal MCP server that exposes Astra specialists as tools.
    Compatible with Ruflo's agent_spawn interface and any MCP client.
    """

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator

    def list_tools(self) -> list[dict]:
        """MCP tools/list response."""
        return list(MCP_TOOL_MANIFEST.values())

    async def call_tool(self, tool_name: str, args: dict) -> MCPToolResult:
        """Route MCP tool call to appropriate Astra specialist."""
        if tool_name not in MCP_TOOL_MANIFEST:
            return MCPToolResult.error(tool_name, f"Unknown tool: {tool_name}")

        try:
            if tool_name == "astra_mirror":
                return await self._call_mirror(args)

            if tool_name == "astra_observer":
                return await self._call_observer(args)

            # All specialist agents route through orchestrator
            specialist = tool_name.replace("astra_", "")
            return await self._call_specialist(specialist, args)

        except Exception as e:
            logger.error("MCP tool call failed: %s — %s", tool_name, e)
            return MCPToolResult.error(tool_name, str(e))

    async def _call_specialist(self, specialist: str, args: dict) -> MCPToolResult:
        if not self.orchestrator:
            return MCPToolResult.error(f"astra_{specialist}", "Orchestrator not configured")

        from backend.core.orchestrator import Orchestrator
        result = await self.orchestrator.run(
            goal=args.get("goal", ""),
            founder_id=args.get("founder_id", "ruflo_caller"),
            session_id=args.get("session_id"),
            constraints={"single_agent": specialist},
        )
        # Extract specialist result
        specialist_result = next(
            (v for k, v in result.get("results", {}).items()),
            result,
        )
        return MCPToolResult.success(f"astra_{specialist}", specialist_result)

    async def _call_mirror(self, args: dict) -> MCPToolResult:
        from proprietary_agent.mirror.founder_mirror import FounderMirror
        mirror = FounderMirror()
        result = await asyncio.to_thread(mirror.review, agent=args["agent"], output=args["output"])
        return MCPToolResult.success("astra_mirror", {
            "verdict": result.verdict,
            "critique": result.critique,
            "questions": result.questions,
            "revised_recommendation": result.revised_recommendation,
        })

    async def _call_observer(self, args: dict) -> MCPToolResult:
        from proprietary_agent.observer.silent_observer import SilentObserver
        from proprietary_agent.graph.decision_graph import DecisionGraph
        graph = DecisionGraph(args["founder_id"])
        obs = SilentObserver(args["founder_id"], graph=graph)
        obs.configure(domains=args.get("domains", []), goals=[])
        alerts = obs.pop_alerts()
        return MCPToolResult.success("astra_observer", {
            "alert_count": len(alerts),
            "alerts": [
                {
                    "summary": a.summary,
                    "source": a.source,
                    "relevance_score": a.relevance_score,
                    "suggested_action": a.suggested_action,
                }
                for a in alerts
            ],
        })

    def to_openai_tools(self) -> list[dict]:
        """Convert manifest to OpenAI function calling format for LiteLLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": spec["description"],
                    "parameters": spec["inputSchema"],
                },
            }
            for name, spec in MCP_TOOL_MANIFEST.items()
        ]


# ------------------------------------------------------------------ #
# Ruflo Memory Adapter
# ------------------------------------------------------------------ #

class RufloMemoryAdapter:
    """
    Wraps Astra's Obsidian vault writes into Ruflo's AgentDB namespace format.
    Falls back to Obsidian if Ruflo is not available.
    """

    def __init__(self, use_ruflo: bool = False, ruflo_endpoint: str | None = None):
        self.use_ruflo = use_ruflo
        self.ruflo_endpoint = ruflo_endpoint

    def write(self, agent: str, founder_id: str, session_id: str, content: dict) -> bool:
        namespace = f"astra_{founder_id}_{agent}"
        if self.use_ruflo and self.ruflo_endpoint:
            return self._ruflo_write(namespace, content, session_id)
        return self._obsidian_write(agent, content)

    def query(self, agent: str, founder_id: str, query: str, top_k: int = 5) -> list[dict]:
        namespace = f"astra_{founder_id}_{agent}"
        if self.use_ruflo and self.ruflo_endpoint:
            return self._ruflo_query(namespace, query, top_k)
        return self._obsidian_read(agent)

    def _ruflo_write(self, namespace: str, content: dict, session_id: str) -> bool:
        try:
            import requests
            resp = requests.post(
                f"{self.ruflo_endpoint}/agentdb/upsert",
                json={"namespace": namespace, "doc": content, "session_id": session_id},
                timeout=5,
            )
            return resp.status_code == 200
        except Exception as e:
            logger.warning("Ruflo AgentDB write failed (%s) — falling back to Obsidian", e)
            return False

    def _ruflo_query(self, namespace: str, query: str, top_k: int) -> list[dict]:
        try:
            import requests
            resp = requests.post(
                f"{self.ruflo_endpoint}/agentdb/search",
                json={"namespace": namespace, "query": query, "top_k": top_k},
                timeout=5,
            )
            if resp.status_code == 200:
                return resp.json().get("results", [])
        except Exception as e:
            logger.warning("Ruflo AgentDB query failed (%s)", e)
        return []

    def _obsidian_write(self, agent: str, content: dict) -> bool:
        try:
            from backend.tools.obsidian_logger import obsidian_log
            obsidian_log(agent, str(content))
            return True
        except Exception as e:
            logger.warning("Obsidian write failed: %s", e)
            return False

    def _obsidian_read(self, agent: str) -> list[dict]:
        try:
            from backend.tools.obsidian_logger import obsidian_read
            result = obsidian_read(agent)
            return [result] if result else []
        except Exception:
            return []


# ------------------------------------------------------------------ #
# SONA Trajectory Tracker
# ------------------------------------------------------------------ #

class SONATracker:
    """
    Feeds Astra execution fingerprints into Ruflo's SONA self-learning system.
    Falls back to local logging if Ruflo is not available.
    """

    def __init__(self, ruflo_endpoint: str | None = None):
        self.ruflo_endpoint = ruflo_endpoint
        self._local_trajectories: list[dict] = []

    def record_trajectory(
        self,
        agent: str,
        task_type: str,
        actions: list[str],
        outcome_score: float,
        latency_ms: float,
        session_id: str = "",
    ) -> None:
        trajectory = {
            "agent": f"astra_{agent}",
            "task_type": task_type,
            "actions": actions,
            "outcome_score": outcome_score,
            "latency_ms": latency_ms,
            "session_id": session_id,
        }
        self._local_trajectories.append(trajectory)

        if self.ruflo_endpoint:
            try:
                import requests
                requests.post(
                    f"{self.ruflo_endpoint}/sona/record",
                    json=trajectory,
                    timeout=3,
                )
            except Exception as e:
                logger.debug("SONA record failed (%s) — stored locally", e)

    def from_fingerprint(self, fingerprint: dict, session_id: str = "") -> None:
        """Convert an execution fingerprint to SONA trajectory entries."""
        for agent in fingerprint.get("agents_used", []):
            timing = fingerprint.get("timing", {})
            actions = [
                tool for tool, status in fingerprint.get("tool_outcomes", {}).items()
                if status == "success"
            ]
            self.record_trajectory(
                agent=agent,
                task_type=self._classify_goal(fingerprint.get("goal", "")),
                actions=actions,
                outcome_score=fingerprint.get("success_score", 0.5),
                latency_ms=timing.get(agent, 0) * 1000,
                session_id=session_id,
            )

    def _classify_goal(self, goal: str) -> str:
        goal_lower = goal.lower()
        if any(w in goal_lower for w in ["saas", "software", "app", "platform"]):
            return "saas_build"
        if any(w in goal_lower for w in ["market", "research", "size", "tam"]):
            return "market_research"
        if any(w in goal_lower for w in ["legal", "nda", "terms", "privacy"]):
            return "legal_setup"
        if any(w in goal_lower for w in ["raise", "investor", "funding", "seed"]):
            return "fundraising"
        if any(w in goal_lower for w in ["landing", "website", "page", "deploy"]):
            return "web_presence"
        return "general"

    def get_local_trajectories(self) -> list[dict]:
        return list(self._local_trajectories)


# ------------------------------------------------------------------ #
# MCPToolBridge — external MCP server discovery
# ------------------------------------------------------------------ #

class MCPToolBridge:
    """
    Wraps any external MCP server as native Astra tools.
    Agents call these the same way they call any other tool — zero integration code.
    """

    def __init__(self):
        self._servers: dict[str, str] = {}  # name → url
        self._tool_cache: dict[str, list[dict]] = {}

    def register_server(self, name: str, url: str):
        self._servers[name] = url
        logger.info("MCP server registered: %s @ %s", name, url)

    async def discover_tools(self, server_name: str) -> list[dict]:
        if server_name in self._tool_cache:
            return self._tool_cache[server_name]

        url = self._servers.get(server_name)
        if not url:
            return []

        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{url}/mcp/v1/tools/list",
                    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                )
                tools = resp.json().get("result", {}).get("tools", [])
                self._tool_cache[server_name] = tools
                return tools
        except Exception as e:
            logger.warning("MCP tool discovery failed for %s: %s", server_name, e)
            return []

    async def call(self, server_name: str, tool_name: str, args: dict) -> dict:
        url = self._servers.get(server_name)
        if not url:
            return {"error": f"MCP server '{server_name}' not registered"}

        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{url}/mcp/v1/tools/call",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": args},
                    },
                )
                result = resp.json().get("result", {})
                return result
        except Exception as e:
            return {"error": str(e)}

    def list_registered_servers(self) -> dict[str, str]:
        return dict(self._servers)
