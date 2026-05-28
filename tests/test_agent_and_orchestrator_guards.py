import json
from unittest.mock import AsyncMock

import pytest

from backend.core.agent import Agent, AgentContext
from backend.core.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_legal_agent_done_blocked_until_required_tools_called(mocker):
    calls = {"llm": 0}

    def fake_llm(_messages):
        calls["llm"] += 1
        if calls["llm"] == 1:
            return json.dumps({"action": "done", "output": {"note": "premature"}})
        if calls["llm"] == 2:
            return json.dumps({"action": "tool", "tool": "format_legal_document", "args": {"doc_type": "privacy_policy", "company_name": "Acme", "content": "ctx"}})
        if calls["llm"] == 3:
            return json.dumps({"action": "tool", "tool": "generate_pdf", "args": {"title": "Privacy", "content": "body"}})
        return json.dumps({"action": "done", "output": {"ok": True}})

    agent = Agent(
        name="legal",
        role="legal",
        tools={
            "format_legal_document": lambda **_kwargs: {"doc_type": "privacy_policy", "formatted_text": "body"},
            "generate_pdf": lambda **_kwargs: {"path": "/tmp/privacy.pdf"},
        },
    )
    agent._call_llm = fake_llm
    mocker.patch("backend.core.events.publish", new=AsyncMock())
    result = await agent.run(AgentContext(goal="g", founder_id="f", session_id="s", shared={}))

    assert result.get("ok") is True
    assert calls["llm"] >= 4


class _FakePlanner:
    name = "planner"
    model = "test"

    def _call_llm(self, _messages):
        return '{"tasks":[]}'


class _FakeAgent:
    def __init__(self, name, outputs):
        self.name = name
        self.outputs = list(outputs)
        self.tools = {}
        self.calls = 0

    async def run(self, _ctx):
        self.calls += 1
        return self.outputs[min(self.calls - 1, len(self.outputs) - 1)]


@pytest.mark.asyncio
async def test_orchestrator_retries_web_when_fallback_detected(mocker):
    planner = _FakePlanner()
    research = _FakeAgent("research", [{"summary": "researched"}])
    web = _FakeAgent("web", [
        {"html": "<!DOCTYPE html><!-- astra-fallback-template --><html></html>"},
        {"html": "<!DOCTYPE html><html><body>custom</body></html>", "url": "https://example.com"},
    ])
    orch = Orchestrator(planner=planner, specialists={"research": research, "web": web})

    mocker.patch("backend.core.events.publish", new=AsyncMock())
    mocker.patch.object(orch, "_expand_goal", new=AsyncMock(return_value="goal"))
    mocker.patch.object(orch, "_initial_plan", new=AsyncMock(return_value=[{"id": "t1", "agent": "research", "instruction": "r", "depends_on": []}]))
    mocker.patch.object(orch, "_replan_with_research", new=AsyncMock(return_value=[{"id": "w1", "agent": "web", "instruction": "w", "depends_on": []}]))
    mocker.patch.object(orch, "_generate_detailed_plan", new=AsyncMock(return_value=[]))
    mocker.patch("backend.tools.obsidian_logger._note_path")
    mocker.patch("backend.tools.obsidian_logger.auto_log_if_missing", return_value=False)
    mocker.patch("backend.tools.obsidian_logger.obsidian_session_index", return_value={"indexed": True})

    await orch.run(goal="g", founder_id="f", session_id="s")
    assert web.calls == 2


@pytest.mark.asyncio
async def test_orchestrator_emits_preview_rich_outputs_for_non_research_agents(mocker):
    planner = _FakePlanner()
    research = _FakeAgent("research", [{"summary": "researched"}])
    web = _FakeAgent("web", [
        {"html": "<!DOCTYPE html><!-- astra-fallback-template --><html></html>"},
        {"html": "<!DOCTYPE html><html><body>custom</body></html>", "url": "https://example.com"},
    ])
    marketing = _FakeAgent("marketing", [{
        "reel_package": {"script": "hook"},
        "ad_images": [{"url": "https://img.example/ad.png", "prompt": "ad"}],
    }])
    technical = _FakeAgent("technical", [{
        "repo_url": "https://github.com/acme/app",
        "deploy_url": "https://acme.vercel.app",
        "files_preview": ["frontend/app/page.tsx", "backend/main.py"],
        "files_in_repo": 24,
    }])
    legal = _FakeAgent("legal", [{
        "documents": [{"doc_type": "privacy_policy", "title": "Privacy Policy", "path": "/tmp/privacy_policy.pdf", "text": "..." }],
    }])
    sales = _FakeAgent("sales", [{
        "leads": [{"company": "Acme Dental"}],
        "sequence": [{"send_day": 1, "subject": "Hi"}],
        "crm_contacts": [{"company": "Acme Dental", "email": "ops@acme.com"}],
    }])
    design = _FakeAgent("design", [{
        "design_spec": {"product": "Acme"},
        "wireframes": [{"page_type": "landing"}],
        "logo_brief": {"direction": "minimal"},
    }])

    specialists = {
        "research": research,
        "web": web,
        "marketing": marketing,
        "technical": technical,
        "legal": legal,
        "sales": sales,
        "design": design,
    }
    orch = Orchestrator(planner=planner, specialists=specialists)

    published: list[dict] = []

    async def capture_publish(_session_id: str, event: dict):
        published.append(event)

    mocker.patch("backend.core.events.publish", new=capture_publish)
    mocker.patch.object(orch, "_expand_goal", new=AsyncMock(return_value="goal"))
    mocker.patch.object(orch, "_initial_plan", new=AsyncMock(return_value=[{"id": "t1", "agent": "research", "instruction": "r", "depends_on": []}]))
    mocker.patch.object(orch, "_replan_with_research", new=AsyncMock(return_value=[
        {"id": "w1", "agent": "web", "instruction": "w", "depends_on": []},
        {"id": "m1", "agent": "marketing", "instruction": "m", "depends_on": []},
        {"id": "t1", "agent": "technical", "instruction": "t", "depends_on": []},
        {"id": "l1", "agent": "legal", "instruction": "l", "depends_on": []},
        {"id": "s1", "agent": "sales", "instruction": "s", "depends_on": []},
        {"id": "d1", "agent": "design", "instruction": "d", "depends_on": []},
    ]))
    mocker.patch.object(orch, "_generate_detailed_plan", new=AsyncMock(return_value=[]))
    mocker.patch("backend.tools.obsidian_logger._note_path")
    mocker.patch("backend.tools.obsidian_logger.auto_log_if_missing", return_value=False)
    mocker.patch("backend.tools.obsidian_logger.obsidian_session_index", return_value={"indexed": True})

    await orch.run(goal="g", founder_id="f", session_id="s")

    goal_done = next(e for e in published if e.get("type") == "goal_done")
    results = goal_done["results"]
    flat = [v for v in results.values() if isinstance(v, dict)]
    assert any(item.get("url", "").startswith("https://") for item in flat)
    assert any((item.get("ad_images") or [{}])[0].get("url", "").startswith("https://") for item in flat if "ad_images" in item)
    assert any(item.get("files_in_repo") == 24 for item in flat)
    assert any(((item.get("documents") or [{}])[0].get("path", "")).endswith(".pdf") for item in flat if "documents" in item)
    assert any(((item.get("crm_contacts") or [{}])[0].get("email")) for item in flat if "crm_contacts" in item)
    assert any(((item.get("wireframes") or [{}])[0].get("page_type") == "landing") for item in flat if "wireframes" in item)
