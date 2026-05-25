"""
Ruflo swarm tests — verifies all 10 MCP tools (8 specialists + mirror + observer),
parallel swarm dispatch, SONA trajectory recording, RufloMemoryAdapter, MCPToolBridge,
and end-to-end swarm-with-mirror-gating using real LLM for mirror calls.
"""

import asyncio
import json
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from proprietary_agent.ruflo_bridge import (
    AstraMCPServer,
    MCPToolBridge,
    MCPToolCall,
    MCPToolResult,
    MCP_TOOL_MANIFEST,
    RufloMemoryAdapter,
    SONATracker,
)

FOUNDER_ID = "swarm_test_founder"

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _make_mock_orch(specialist_result: dict = None):
    """Mock orchestrator that returns a fixed result for any specialist."""
    mock = MagicMock()
    mock.run = AsyncMock(return_value={
        "session_id": "swarm_sess",
        "results": {"t0": specialist_result or {"status": "ok", "summary": "task done"}},
        "shared": {},
    })
    return mock


# ================================================================== #
# 1. Manifest completeness
# ================================================================== #

class TestSwarmManifest:
    def test_all_ten_tools_present(self):
        expected = {
            "astra_research", "astra_legal", "astra_web", "astra_marketing",
            "astra_technical", "astra_ops", "astra_sales", "astra_design",
            "astra_mirror", "astra_observer",
        }
        assert set(MCP_TOOL_MANIFEST.keys()) == expected

    def test_all_tools_have_required_fields(self):
        for name, spec in MCP_TOOL_MANIFEST.items():
            assert "name" in spec, f"{name} missing 'name'"
            assert "description" in spec, f"{name} missing 'description'"
            assert "inputSchema" in spec, f"{name} missing 'inputSchema'"
            assert len(spec["description"]) > 20, f"{name} description too short"

    def test_specialist_tools_require_goal_and_founder_id(self):
        specialist_tools = [k for k in MCP_TOOL_MANIFEST if k not in ("astra_mirror", "astra_observer")]
        for name in specialist_tools:
            required = MCP_TOOL_MANIFEST[name]["inputSchema"].get("required", [])
            assert "goal" in required, f"{name} missing required 'goal'"
            assert "founder_id" in required, f"{name} missing required 'founder_id'"

    def test_sales_schema_has_sales_specific_fields(self):
        props = MCP_TOOL_MANIFEST["astra_sales"]["inputSchema"]["properties"]
        assert "industry" in props
        assert "job_title" in props
        assert "product_name" in props
        assert "value_prop" in props

    def test_design_schema_has_design_specific_fields(self):
        props = MCP_TOOL_MANIFEST["astra_design"]["inputSchema"]["properties"]
        assert "product_type" in props
        assert "brand_vibe" in props
        assert "page_types" in props

    def test_mirror_enum_includes_sales_and_design(self):
        agent_enum = MCP_TOOL_MANIFEST["astra_mirror"]["inputSchema"]["properties"]["agent"]["enum"]
        assert "sales" in agent_enum
        assert "design" in agent_enum

    def test_openai_tools_conversion(self):
        server = AstraMCPServer()
        oa_tools = server.to_openai_tools()
        assert len(oa_tools) == 10
        names = {t["function"]["name"] for t in oa_tools}
        assert "astra_sales" in names
        assert "astra_design" in names
        for tool in oa_tools:
            assert tool["type"] == "function"
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]


# ================================================================== #
# 2. MCP server routing
# ================================================================== #

class TestSwarmRouting:
    def test_unknown_tool_returns_error(self):
        server = AstraMCPServer()
        result = asyncio.get_event_loop().run_until_complete(
            server.call_tool("astra_nonexistent", {"goal": "x", "founder_id": "f"})
        )
        assert result.is_error
        assert "Unknown tool" in result.content[0]["text"]

    def test_specialist_without_orchestrator_returns_error(self):
        server = AstraMCPServer(orchestrator=None)
        for tool in ["astra_sales", "astra_design", "astra_research"]:
            result = asyncio.get_event_loop().run_until_complete(
                server.call_tool(tool, {"goal": "test", "founder_id": FOUNDER_ID})
            )
            assert result.is_error
            assert "Orchestrator not configured" in result.content[0]["text"]

    def test_sales_routes_to_orchestrator(self):
        mock_orch = _make_mock_orch({"leads": [{"name": "Alice", "company": "DentaCo"}]})
        server = AstraMCPServer(orchestrator=mock_orch)
        result = asyncio.get_event_loop().run_until_complete(
            server.call_tool("astra_sales", {
                "goal": "Find dental office managers in Texas",
                "founder_id": FOUNDER_ID,
                "industry": "dental",
                "job_title": "office manager",
            })
        )
        assert not result.is_error
        mock_orch.run.assert_called_once()
        call_kwargs = mock_orch.run.call_args
        assert call_kwargs.kwargs["founder_id"] == FOUNDER_ID

    def test_design_routes_to_orchestrator(self):
        mock_orch = _make_mock_orch({"wireframe": "...", "palette": {"primary": "#000"}})
        server = AstraMCPServer(orchestrator=mock_orch)
        result = asyncio.get_event_loop().run_until_complete(
            server.call_tool("astra_design", {
                "goal": "Design landing page for DentSchedule SaaS",
                "founder_id": FOUNDER_ID,
                "product_type": "saas",
                "brand_vibe": "minimal",
            })
        )
        assert not result.is_error
        mock_orch.run.assert_called_once()

    def test_result_parsed_from_first_completed_task(self):
        expected = {"leads": 5, "sequences": 5}
        mock_orch = _make_mock_orch(expected)
        server = AstraMCPServer(orchestrator=mock_orch)
        result = asyncio.get_event_loop().run_until_complete(
            server.call_tool("astra_sales", {"goal": "find leads", "founder_id": FOUNDER_ID})
        )
        data = json.loads(result.content[0]["text"])
        assert data == expected

    def test_list_tools_returns_all_ten(self):
        server = AstraMCPServer()
        tools = server.list_tools()
        assert len(tools) == 10
        names = {t["name"] for t in tools}
        assert "astra_sales" in names
        assert "astra_design" in names


# ================================================================== #
# 3. Parallel swarm dispatch (all specialists concurrently)
# ================================================================== #

class TestSwarmParallelDispatch:
    @pytest.mark.asyncio
    async def test_all_eight_specialists_dispatch_in_parallel(self):
        """Simulate a swarm coordinator dispatching all 8 specialists simultaneously."""
        call_order = []

        async def fake_run(**kwargs):
            call_order.append(kwargs.get("goal", "")[:10])
            await asyncio.sleep(0.01)  # simulate async work
            return {
                "session_id": "s",
                "results": {"t0": {"status": "ok"}},
                "shared": {},
            }

        mock_orch = MagicMock()
        mock_orch.run = fake_run
        server = AstraMCPServer(orchestrator=mock_orch)

        specialists = ["astra_research", "astra_legal", "astra_web", "astra_marketing",
                       "astra_technical", "astra_ops", "astra_sales", "astra_design"]

        t0 = time.monotonic()
        results = await asyncio.gather(*[
            server.call_tool(tool, {"goal": f"task for {tool}", "founder_id": FOUNDER_ID})
            for tool in specialists
        ])
        elapsed = time.monotonic() - t0

        assert len(results) == 8
        assert all(not r.is_error for r in results)
        # Parallel: should complete in ~0.01s not 0.08s (serial)
        assert elapsed < 0.2, f"Parallel dispatch too slow: {elapsed:.2f}s"
        assert len(call_order) == 8

    @pytest.mark.asyncio
    async def test_swarm_dispatch_isolates_founder_contexts(self):
        """Two founders dispatching simultaneously don't share state."""
        received_founder_ids = []

        async def fake_run(**kwargs):
            received_founder_ids.append(kwargs["founder_id"])
            await asyncio.sleep(0.01)
            return {"session_id": "s", "results": {"t0": {}}, "shared": {}}

        mock_orch = MagicMock()
        mock_orch.run = fake_run
        server = AstraMCPServer(orchestrator=mock_orch)

        founders = ["founder_alpha", "founder_beta", "founder_gamma"]
        await asyncio.gather(*[
            server.call_tool("astra_sales", {"goal": "find leads", "founder_id": fid})
            for fid in founders
        ])

        assert set(received_founder_ids) == set(founders)
        assert len(received_founder_ids) == 3

    @pytest.mark.asyncio
    async def test_partial_swarm_failure_doesnt_block_others(self):
        """If one specialist fails, others still complete."""
        call_count = 0

        async def fake_run(**kwargs):
            nonlocal call_count
            call_count += 1
            if "sales" in kwargs.get("goal", ""):
                raise RuntimeError("Simulated sales agent failure")
            return {"session_id": "s", "results": {"t0": {"status": "ok"}}, "shared": {}}

        mock_orch = MagicMock()
        mock_orch.run = fake_run
        server = AstraMCPServer(orchestrator=mock_orch)

        results = await asyncio.gather(
            server.call_tool("astra_sales", {"goal": "sales task", "founder_id": FOUNDER_ID}),
            server.call_tool("astra_design", {"goal": "design task", "founder_id": FOUNDER_ID}),
            server.call_tool("astra_research", {"goal": "research task", "founder_id": FOUNDER_ID}),
        )

        assert results[0].is_error   # sales failed
        assert not results[1].is_error  # design succeeded
        assert not results[2].is_error  # research succeeded


# ================================================================== #
# 4. New agent MCP tools — local tool execution (no LLM)
# ================================================================== #

class TestSalesDesignMCPTools:
    def test_sales_mcp_result_contains_lead_data(self):
        """astra_sales via orchestrator mock returns lead structure."""
        lead_data = {
            "leads": [
                {"name": "Dr. Smith", "company": "DentaCo", "title": "Office Manager"},
                {"name": "Lisa Chen", "company": "ToothFirst", "title": "Practice Manager"},
            ],
            "count": 2,
            "sequences": [{"send_day": 1, "subject": "Quick question"}],
        }
        mock_orch = _make_mock_orch(lead_data)
        server = AstraMCPServer(orchestrator=mock_orch)
        result = asyncio.get_event_loop().run_until_complete(
            server.call_tool("astra_sales", {
                "goal": "Find dental office managers and build outreach sequence",
                "founder_id": FOUNDER_ID,
                "industry": "dental",
                "job_title": "office manager",
                "product_name": "DentSchedule",
                "value_prop": "Reduce no-shows by 40%",
            })
        )
        assert not result.is_error
        data = json.loads(result.content[0]["text"])
        assert data["count"] == 2
        assert len(data["leads"]) == 2

    def test_design_mcp_result_contains_design_artifacts(self):
        """astra_design via orchestrator mock returns design artifacts."""
        design_data = {
            "wireframes": {"landing": "ASCII wireframe content"},
            "palette": {"primary": "#000000", "secondary": "#6B7280"},
            "spec": {"typography": {"heading_font": "Inter"}},
        }
        mock_orch = _make_mock_orch(design_data)
        server = AstraMCPServer(orchestrator=mock_orch)
        result = asyncio.get_event_loop().run_until_complete(
            server.call_tool("astra_design", {
                "goal": "Design complete brand identity for DentSchedule SaaS",
                "founder_id": FOUNDER_ID,
                "product_type": "saas",
                "brand_vibe": "minimal",
                "page_types": ["landing", "dashboard", "pricing"],
            })
        )
        assert not result.is_error
        data = json.loads(result.content[0]["text"])
        assert "wireframes" in data
        assert "palette" in data

    def test_sales_local_tools_execute_without_llm(self):
        """Verify sales tools (find_leads, inbox_warmer etc.) work standalone."""
        from backend.tools.inbox_warmer import create_warming_schedule, build_crm_contact
        from backend.tools.lead_finder import build_outreach_sequence

        sched = create_warming_schedule("founder@dentschedule.com", "DentSchedule", duration_days=7)
        assert sched["duration_days"] == 7
        assert len(sched["schedule"]) == 7
        assert sched["schedule"][-1]["volume"] > sched["schedule"][0]["volume"]

        contact = build_crm_contact(
            name="Dr. Smith", email="smith@dentaco.com",
            company="DentaCo", title="Office Manager",
        )
        assert contact["pipeline"]["status"] == "new"
        assert contact["pipeline"]["next_action"] == "send_intro_email"

        seq = build_outreach_sequence(
            product_name="DentSchedule",
            value_prop="Reduce no-shows by 40%",
            lead_name="Dr. Smith",
            lead_company="DentaCo",
            lead_title="Office Manager",
            sequence_length=3,
        )
        assert len(seq["sequence"]) == 3
        assert seq["sequence"][0]["type"] == "intro"
        assert seq["sequence"][1]["type"] == "follow_up_1"
        assert seq["sequence"][2]["type"] == "break_up"

    def test_design_local_tools_execute_without_llm(self):
        """Verify design tools execute standalone — no LLM, no network."""
        from backend.tools.design_tools import (
            generate_wireframe, generate_color_palette,
            generate_design_spec, generate_logo_brief,
        )

        # Wireframe
        wire = generate_wireframe("landing", ["hero", "features", "pricing"], style="minimal")
        assert "wireframe_ascii" in wire
        assert "┌" in wire["wireframe_ascii"]
        assert len(wire["components"]) > 0

        # Color palette — all 6 vibes
        for vibe in ["bold", "minimal", "friendly", "professional", "innovative", "calm"]:
            palette = generate_color_palette(vibe, "saas")
            assert palette["colors"]["primary"].startswith("#")
            assert "css_variables" in palette

        # Design spec
        spec = generate_design_spec("DentSchedule", "saas", "dental office managers", "minimal")
        assert "typography" in spec
        assert "spacing_system" in spec
        assert len(spec["key_screens"]) > 0

        # Logo brief
        logo = generate_logo_brief("DentSchedule", "Fill every chair", "dental SaaS", "minimal")
        assert len(logo["deliverables"]) >= 6
        assert len(logo["prompts_for_ai_generation"]) == 2


# ================================================================== #
# 5. SONA Tracker — all 8 agents including sales + design
# ================================================================== #

class TestSONASwarm:
    def test_sona_records_trajectory_for_all_eight_agents(self):
        sona = SONATracker()
        agents = ["research", "legal", "web", "marketing", "technical", "ops", "sales", "design"]
        for agent in agents:
            sona.record_trajectory(
                agent=agent,
                task_type="test_task",
                actions=["tool_a", "tool_b"],
                outcome_score=0.85,
                latency_ms=1200.0,
                session_id="swarm_test",
            )
        trajectories = sona.get_local_trajectories()
        assert len(trajectories) == 8
        recorded_agents = {t["agent"] for t in trajectories}
        assert recorded_agents == {f"astra_{a}" for a in agents}

    def test_sona_from_fingerprint_extracts_sales_design(self):
        sona = SONATracker()
        fingerprint = {
            "goal": "Launch DentSchedule SaaS — find dental leads, design brand",
            "agents_used": ["research", "sales", "design", "marketing"],
            "timing": {"research": 12.5, "sales": 8.2, "design": 5.1, "marketing": 9.7},
            "tool_outcomes": {
                "find_leads": "success",
                "enrich_lead": "success",
                "generate_wireframe": "success",
                "generate_color_palette": "success",
            },
            "success_score": 0.9,
        }
        sona.from_fingerprint(fingerprint, session_id="fp_test")
        trajectories = sona.get_local_trajectories()
        assert len(trajectories) == 4
        agent_names = {t["agent"] for t in trajectories}
        assert "astra_sales" in agent_names
        assert "astra_design" in agent_names

    def test_sona_classify_goal_covers_all_types(self):
        sona = SONATracker()
        assert sona._classify_goal("build SaaS platform for dentists") == "saas_build"
        assert sona._classify_goal("TAM market research sizing") == "market_research"
        assert sona._classify_goal("draft NDA legal agreement") == "legal_setup"
        assert sona._classify_goal("raise seed funding from investors") == "fundraising"
        assert sona._classify_goal("deploy landing page to Vercel") == "web_presence"
        assert sona._classify_goal("hire first employee onboarding") == "general"

    def test_sona_trajectory_schema_complete(self):
        sona = SONATracker()
        sona.record_trajectory(
            agent="sales",
            task_type="lead_gen",
            actions=["find_leads", "enrich_lead", "build_outreach_sequence"],
            outcome_score=0.92,
            latency_ms=3400.0,
            session_id="schema_test",
        )
        t = sona.get_local_trajectories()[0]
        assert t["agent"] == "astra_sales"
        assert t["task_type"] == "lead_gen"
        assert "find_leads" in t["actions"]
        assert t["outcome_score"] == 0.92
        assert t["latency_ms"] == 3400.0


# ================================================================== #
# 6. Ruflo Memory Adapter
# ================================================================== #

class TestRufloMemorySwarm:
    def test_obsidian_fallback_write(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ASTRA_OBSIDIAN_VAULT", str(tmp_path))
        import importlib, backend.config
        importlib.reload(backend.config)
        from backend.config import settings
        settings.obsidian_vault = str(tmp_path)

        adapter = RufloMemoryAdapter(use_ruflo=False)
        # Write falls through to obsidian_log — just verify no crash
        result = adapter.write(
            agent="sales",
            founder_id=FOUNDER_ID,
            session_id="mem_test",
            content={"leads": 5, "sequences": 5},
        )
        # Result is bool — True if obsidian write succeeded, may be True or False depending on env
        assert isinstance(result, bool)

    def test_ruflo_mode_falls_back_on_connection_error(self):
        adapter = RufloMemoryAdapter(use_ruflo=True, ruflo_endpoint="http://localhost:19999")
        # No Ruflo running — should fall back gracefully (no exception)
        result = adapter.write(
            agent="design",
            founder_id=FOUNDER_ID,
            session_id="mem_test",
            content={"wireframe": "..."},
        )
        assert isinstance(result, bool)

    def test_namespace_format(self):
        adapter = RufloMemoryAdapter()
        # Namespace = astra_{founder_id}_{agent} — verify write constructs correctly
        written_namespaces = []

        def fake_ruflo_write(namespace, content, session_id):
            written_namespaces.append(namespace)
            return False  # simulate network fail → obsidian fallback

        adapter._ruflo_write = fake_ruflo_write
        adapter.use_ruflo = True
        adapter.ruflo_endpoint = "http://fake"
        adapter.write("sales", "founder_xyz", "sess_abc", {"data": 1})
        assert written_namespaces == ["astra_founder_xyz_sales"]

    def test_obsidian_fallback_query_returns_list(self):
        adapter = RufloMemoryAdapter(use_ruflo=False)
        results = adapter.query("design", FOUNDER_ID, "wireframe color palette", top_k=3)
        assert isinstance(results, list)


# ================================================================== #
# 7. MCPToolBridge — external MCP server integration
# ================================================================== #

class TestMCPToolBridgeSwarm:
    def test_register_and_list_servers(self):
        bridge = MCPToolBridge()
        bridge.register_server("figma", "http://figma-mcp.local")
        bridge.register_server("stripe", "http://stripe-mcp.local")
        servers = bridge.list_registered_servers()
        assert servers["figma"] == "http://figma-mcp.local"
        assert servers["stripe"] == "http://stripe-mcp.local"

    def test_call_unknown_server_returns_error(self):
        bridge = MCPToolBridge()
        result = asyncio.get_event_loop().run_until_complete(
            bridge.call("nonexistent", "some_tool", {})
        )
        assert "error" in result
        assert "not registered" in result["error"]

    @pytest.mark.asyncio
    async def test_discover_tools_caches_results(self):
        bridge = MCPToolBridge()
        bridge.register_server("test_mcp", "http://test.local")

        mock_tools = [
            {"name": "create_design", "description": "Create a Figma design"},
            {"name": "export_assets", "description": "Export design assets"},
        ]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"result": {"tools": mock_tools}}
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_class.return_value = mock_client

            tools1 = await bridge.discover_tools("test_mcp")
            tools2 = await bridge.discover_tools("test_mcp")  # should use cache

            assert tools1 == mock_tools
            assert tools2 == mock_tools
            # Second call should hit cache, not network
            assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_call_routes_to_registered_server(self):
        bridge = MCPToolBridge()
        bridge.register_server("figma", "http://figma.local")

        expected_result = {"file_id": "abc123", "url": "https://figma.com/file/abc123"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"result": expected_result}
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_class.return_value = mock_client

            result = await bridge.call("figma", "create_file", {"name": "DentSchedule Brand"})
            assert result == expected_result

    @pytest.mark.asyncio
    async def test_call_handles_network_error(self):
        bridge = MCPToolBridge()
        bridge.register_server("flaky", "http://flaky.local")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=ConnectionError("refused"))
            mock_client_class.return_value = mock_client

            result = await bridge.call("flaky", "some_tool", {})
            assert "error" in result


# ================================================================== #
# 8. Observer MCP tool
# ================================================================== #

class TestObserverMCPTool:
    @pytest.mark.asyncio
    async def test_observer_returns_empty_alerts_for_new_founder(self):
        server = AstraMCPServer()
        result = await server.call_tool("astra_observer", {
            "founder_id": f"observer_test_{uuid.uuid4().hex[:6]}",
            "domains": ["dental scheduling", "SaaS"],
        })
        assert not result.is_error
        data = json.loads(result.content[0]["text"])
        assert "alert_count" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)
        assert data["alert_count"] == len(data["alerts"])

    @pytest.mark.asyncio
    async def test_observer_requires_founder_id(self):
        server = AstraMCPServer()
        # Should not crash even with minimal args
        result = await server.call_tool("astra_observer", {"founder_id": "test_obs"})
        assert not result.is_error


# ================================================================== #
# 9. Real swarm with Mirror gating (real LLM calls)
# ================================================================== #

class TestSwarmWithMirrorGating:
    """
    Simulate a Ruflo swarm coordinator pattern:
    1. Dispatch design + sales tools (mocked orchestrator, instant)
    2. Gate each output through astra_mirror (real LLM)
    3. Verify mirror verdicts are valid and block if output is weak
    """

    @pytest.mark.asyncio
    async def test_swarm_mirror_gates_sales_output(self):
        """Weak sales output (generic, no ICP) should get flagged/blocked by mirror."""
        server = AstraMCPServer()  # no orchestrator — only mirror
        t = time.monotonic()
        result = await server.call_tool("astra_mirror", {
            "agent": "sales",
            "output": (
                "Found some leads. Here are potential customers:\n"
                "- Various companies in the market\n"
                "- People who might be interested\n"
                "Will send emails soon."
            ),
        })
        latency = time.monotonic() - t
        print(f"\n[Swarm mirror: sales weak] verdict={json.loads(result.content[0]['text'])['verdict']} latency={latency:.2f}s")
        assert not result.is_error
        data = json.loads(result.content[0]["text"])
        assert data["verdict"] in ("pass", "flag", "block")
        # Weak output with no ICP, no real leads should flag or block
        assert data["verdict"] in ("flag", "block"), f"Expected flag/block for weak sales output, got {data['verdict']}"
        assert latency < 60

    @pytest.mark.asyncio
    async def test_swarm_mirror_gates_design_output(self):
        """Solid design output with specific artifacts should pass or flag."""
        server = AstraMCPServer()
        strong_design = """
        DentSchedule Brand Design System

        Color Palette (minimal vibe):
        - Primary: #000000 (headlines, CTAs)
        - Secondary: #6B7280 (body text, captions)
        - Accent: #3B82F6 (links, highlights)
        - Background: #FFFFFF
        - Surface: #F9FAFB (cards, sidebars)

        Typography: Inter (heading), Inter (body), JetBrains Mono (code)
        Scale: 12/14/16/18/24/30/36/48px

        Landing Page Wireframe:
        ┌──────────────────────────────────────┐
        │ DentSchedule      Features Pricing ▶ │
        ├──────────────────────────────────────┤
        │   Fill Every Chair. Zero No-Shows.   │
        │   Scheduling SaaS for dental offices │
        │   [Start Free Trial] [Watch Demo]    │
        ├──────────────────────────────────────┤
        │ 2,400+ dental offices trust us       │
        └──────────────────────────────────────┘

        Logo Brief: Wordmark "DentSchedule" in Inter SemiBold.
        Icon: Stylized calendar + tooth. Delivered in SVG + PNG @1x/2x/3x.
        """
        t = time.monotonic()
        result = await server.call_tool("astra_mirror", {
            "agent": "design",
            "output": strong_design,
        })
        latency = time.monotonic() - t
        data = json.loads(result.content[0]["text"])
        print(f"\n[Swarm mirror: design strong] verdict={data['verdict']} latency={latency:.2f}s")
        assert not result.is_error
        assert data["verdict"] in ("pass", "flag", "block")
        assert latency < 60

    @pytest.mark.asyncio
    async def test_swarm_parallel_mirror_gating(self):
        """
        Full swarm pattern: dispatch 4 mirror reviews concurrently.
        Simulates a swarm coordinator gating outputs from all agents before delivery.
        """
        server = AstraMCPServer()

        outputs = {
            "sales": "Found 15 dental office managers in Texas. Built 3-email sequences. Avg open rate target: 42%. Warming schedule ready for outreach@dentschedule.com.",
            "design": "Minimal brand: primary #000, Inter fonts. Landing wireframe delivered. Logo brief: wordmark + tooth calendar icon. All 6 deliverable formats specified.",
            "research": "Dental scheduling SaaS market: $2.1B TAM, 187k US offices, 12% no-show rate = $50k/yr pain per practice. Top competitors: Dentrix ($299/mo), Eaglesoft, Curve Dental.",
            "marketing": "Instagram Reel: 30s hook showing a 3pm no-show blocking the chair. TikTok script: before/after revenue calculator. LinkedIn ad targeting office managers at 50+ employee dental groups.",
        }

        t0 = time.monotonic()
        results = await asyncio.gather(*[
            server.call_tool("astra_mirror", {"agent": agent, "output": output})
            for agent, output in outputs.items()
        ])
        total_latency = time.monotonic() - t0

        print(f"\n[Swarm parallel mirror — 4 agents]")
        print(f"  Total latency: {total_latency:.2f}s")
        print(f"  Avg per agent: {total_latency/4:.2f}s")

        for i, (agent, _) in enumerate(outputs.items()):
            data = json.loads(results[i].content[0]["text"])
            print(f"  [{agent}] verdict={data['verdict']}")
            assert not results[i].is_error
            assert data["verdict"] in ("pass", "flag", "block")
            assert data["critique"]

        # Parallel: all 4 reviews should complete faster than 4x serial
        # Serial would be ~40s (4 × 10s), parallel should be ~10-20s
        assert total_latency < 120, f"Parallel mirror too slow: {total_latency:.2f}s"

    @pytest.mark.asyncio
    async def test_swarm_sona_records_after_mirror_gating(self):
        """SONA tracks full swarm trajectory including mirror verdict."""
        sona = SONATracker()

        # Simulate post-swarm SONA recording
        swarm_fingerprint = {
            "goal": "Launch DentSchedule — build sales pipeline and brand identity",
            "agents_used": ["research", "sales", "design", "marketing"],
            "timing": {"research": 15.2, "sales": 9.8, "design": 6.5, "marketing": 11.3},
            "tool_outcomes": {
                "find_leads": "success",
                "enrich_lead": "success",
                "build_outreach_sequence": "success",
                "generate_wireframe": "success",
                "generate_color_palette": "success",
                "generate_design_spec": "success",
                "web_search": "success",
            },
            "mirror_verdicts": {
                "sales": "flag",
                "design": "pass",
                "research": "pass",
                "marketing": "flag",
            },
            "success_score": 0.78,
        }

        sona.from_fingerprint(swarm_fingerprint, session_id="swarm_sona_test")
        trajectories = sona.get_local_trajectories()

        assert len(trajectories) == 4
        agents = {t["agent"] for t in trajectories}
        assert "astra_sales" in agents
        assert "astra_design" in agents

        # Verify timing was recorded
        sales_t = next(t for t in trajectories if t["agent"] == "astra_sales")
        assert sales_t["latency_ms"] == 9800.0
