import json

from backend.tools.company_brain_mcp import handle_request


def _call_tool(name, arguments=None, request_id=1):
    return handle_request({
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    })


def _structured(response):
    assert response["jsonrpc"] == "2.0"
    assert "error" not in response
    return response["result"]["structuredContent"]


def test_company_brain_mcp_lists_core_tools():
    response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response["jsonrpc"] == "2.0"
    tool_names = {tool["name"] for tool in response["result"]["tools"]}
    assert "company_brain_search" in tool_names
    assert "company_brain_ask" in tool_names
    assert "company_brain_agent_context" in tool_names
    assert "company_brain_import_sources" in tool_names
    assert "company_brain_status" in tool_names


def test_company_brain_mcp_adds_and_searches_records(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_mcp"

    added = _structured(_call_tool("company_brain_add_record", {
        "founder_id": founder_id,
        "title": "Sales source of truth",
        "content": "Use founder-led sales first, then expand to product-led onboarding.",
        "source": "manual",
        "canonical": True,
    }))
    assert added["ok"] is True

    searched = _structured(_call_tool("company_brain_search", {
        "founder_id": founder_id,
        "query": "product-led onboarding",
        "limit": 5,
    }))
    assert searched["count"] == 1
    assert searched["results"][0]["title"] == "Sales source of truth"

    context = _structured(_call_tool("company_brain_agent_context", {
        "founder_id": founder_id,
        "query": "sales onboarding",
    }))
    assert context["ok"] is True
    assert context["canonical_sources"][0]["title"] == "Sales source of truth"

    asked = _structured(_call_tool("company_brain_ask", {
        "founder_id": founder_id,
        "question": "What is our sales onboarding strategy?",
        "limit": 5,
    }))
    assert asked["ok"] is True
    assert asked["citations"][0]["title"] == "Sales source of truth"


def test_company_brain_mcp_resources_read_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    founder_id = "founder_resource"
    _structured(_call_tool("company_brain_add_record", {
        "founder_id": founder_id,
        "title": "Support rule",
        "content": "Escalate enterprise support tickets within one hour.",
        "source": "manual",
    }))

    listed = handle_request({"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {"founder_id": founder_id}})
    resource = listed["result"]["resources"][0]
    assert resource["uri"] == f"astra://company-brain/{founder_id}"

    read = handle_request({"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": resource["uri"]}})
    payload = json.loads(read["result"]["contents"][0]["text"])
    assert payload["ok"] is True
    assert payload["record_count"] == 1
    assert "github" in payload["importers"]


def test_company_brain_mcp_configures_long_sync_interval(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    configured = _structured(_call_tool("company_brain_configure_sync", {
        "founder_id": "founder_sync",
        "enabled": True,
        "sources": ["github"],
        "interval_minutes": 240,
    }))

    assert configured["ok"] is True
    assert configured["sync"]["interval_minutes"] == 240
    assert configured["sync"]["sources"] == ["github"]
