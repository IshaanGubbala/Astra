"""Stdio JSON-RPC bridge for company-brain agent access.

This module intentionally avoids a runtime MCP dependency. It implements the
small JSON-RPC surface IDE agents need: list tools, call tools, and read a
founder-scoped company-brain resource.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable

from backend.tools.company_brain import (
    add_company_brain_record,
    ask_company_brain,
    company_brain_agent_context,
    configure_company_brain_sync,
    get_company_brain,
    get_company_brain_sync_status,
    ingest_company_brain_records,
    maintain_company_brain,
    run_company_brain_sync,
    search_company_brain,
)
from backend.tools.company_brain_connectors import IMPORTERS, import_company_brain_sources


DEFAULT_FOUNDER_ID = "founder_001"
SERVER_INFO = {"name": "astra-company-brain", "version": "0.1.0"}


def _default_founder_id() -> str:
    return os.environ.get("ASTRA_FOUNDER_ID") or DEFAULT_FOUNDER_ID


def _json_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "company_brain_search",
        "description": "Search Astra's company brain for relevant records.",
        "inputSchema": _json_schema({
            "founder_id": {"type": "string", "description": "Founder/company id. Defaults to ASTRA_FOUNDER_ID."},
            "query": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 8},
        }, ["query"]),
    },
    {
        "name": "company_brain_ask",
        "description": "Answer a question from company-brain records and return explicit citations.",
        "inputSchema": _json_schema({
            "founder_id": {"type": "string", "description": "Founder/company id. Defaults to ASTRA_FOUNDER_ID."},
            "question": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 8},
        }, ["question"]),
    },
    {
        "name": "company_brain_agent_context",
        "description": "Return compact records, canonical sources, relationships, proposals, and sync state for an agent task.",
        "inputSchema": _json_schema({
            "founder_id": {"type": "string", "description": "Founder/company id. Defaults to ASTRA_FOUNDER_ID."},
            "query": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 8},
        }, ["query"]),
    },
    {
        "name": "company_brain_add_record",
        "description": "Add a manual memory or normalized source record to the company brain.",
        "inputSchema": _json_schema({
            "founder_id": {"type": "string", "description": "Founder/company id. Defaults to ASTRA_FOUNDER_ID."},
            "source": {"type": "string", "default": "manual"},
            "title": {"type": "string"},
            "content": {"type": "string"},
            "kind": {"type": "string", "default": "note"},
            "url": {"type": "string", "default": ""},
            "canonical": {"type": "boolean", "default": False},
            "stale_risk": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
        }, ["title", "content"]),
    },
    {
        "name": "company_brain_ingest_records",
        "description": "Bulk-ingest normalized records from an external connector or script.",
        "inputSchema": _json_schema({
            "founder_id": {"type": "string", "description": "Founder/company id. Defaults to ASTRA_FOUNDER_ID."},
            "source": {"type": "string"},
            "records": {"type": "array", "items": {"type": "object"}},
        }, ["source", "records"]),
    },
    {
        "name": "company_brain_import_sources",
        "description": "Import live connected sources such as GitHub, Slack, Notion, Google Drive, Gmail, Linear, Zendesk, and Confluence.",
        "inputSchema": _json_schema({
            "founder_id": {"type": "string", "description": "Founder/company id. Defaults to ASTRA_FOUNDER_ID."},
            "sources": {"type": "array", "items": {"type": "string", "enum": sorted(IMPORTERS)}},
            "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
        }),
    },
    {
        "name": "company_brain_configure_sync",
        "description": "Enable or pause continuous company-brain sync.",
        "inputSchema": _json_schema({
            "founder_id": {"type": "string", "description": "Founder/company id. Defaults to ASTRA_FOUNDER_ID."},
            "enabled": {"type": "boolean", "default": True},
            "sources": {"type": "array", "items": {"type": "string", "enum": sorted(IMPORTERS)}},
            "interval_minutes": {"type": "integer", "minimum": 5, "maximum": 1440, "default": 60},
        }),
    },
    {
        "name": "company_brain_run_sync",
        "description": "Run the configured provider import and metadata sync now.",
        "inputSchema": _json_schema({
            "founder_id": {"type": "string", "description": "Founder/company id. Defaults to ASTRA_FOUNDER_ID."},
            "force": {"type": "boolean", "default": True},
        }),
    },
    {
        "name": "company_brain_maintain",
        "description": "Detect stale records, canonical gaps, and contradictions.",
        "inputSchema": _json_schema({
            "founder_id": {"type": "string", "description": "Founder/company id. Defaults to ASTRA_FOUNDER_ID."},
        }),
    },
    {
        "name": "company_brain_status",
        "description": "Return source counts, maintenance stats, sync state, and supported importers.",
        "inputSchema": _json_schema({
            "founder_id": {"type": "string", "description": "Founder/company id. Defaults to ASTRA_FOUNDER_ID."},
        }),
    },
]


def _founder(args: dict[str, Any]) -> str:
    return str(args.get("founder_id") or _default_founder_id())


def _limit(args: dict[str, Any], default: int = 8) -> int:
    try:
        return max(1, min(int(args.get("limit", default)), 100))
    except Exception:
        return default


def _int_arg(args: dict[str, Any], key: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(int(args.get(key, default)), maximum))
    except Exception:
        return default


def _status(args: dict[str, Any]) -> dict[str, Any]:
    founder_id = _founder(args)
    brain = get_company_brain(founder_id)
    sync = get_company_brain_sync_status(founder_id).get("sync", {})
    return {
        "ok": True,
        "founder_id": founder_id,
        "record_count": len(brain.get("records", [])),
        "relationship_count": len(brain.get("relationships", [])),
        "open_proposal_count": len([p for p in brain.get("proposals", []) if p.get("status") == "open"]),
        "sources": list(brain.get("sources", {}).values()),
        "maintenance": brain.get("maintenance", {}),
        "sync": sync,
        "importers": sorted(IMPORTERS),
    }


def _dispatch_table() -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    return {
        "company_brain_search": lambda args: search_company_brain(_founder(args), str(args.get("query", "")), _limit(args)),
        "company_brain_ask": lambda args: ask_company_brain(_founder(args), str(args.get("question", "")), _limit(args)),
        "company_brain_agent_context": lambda args: company_brain_agent_context(_founder(args), str(args.get("query", "")), _limit(args)),
        "company_brain_add_record": lambda args: add_company_brain_record(
            _founder(args),
            str(args.get("source") or "manual"),
            str(args.get("title") or ""),
            str(args.get("content") or ""),
            kind=str(args.get("kind") or "note"),
            url=str(args.get("url") or ""),
            canonical=bool(args.get("canonical", False)),
            stale_risk=str(args.get("stale_risk") or "medium"),
        ),
        "company_brain_ingest_records": lambda args: ingest_company_brain_records(
            _founder(args),
            str(args.get("source") or "manual"),
            list(args.get("records") or []),
        ),
        "company_brain_import_sources": lambda args: import_company_brain_sources(
            _founder(args),
            list(args.get("sources") or IMPORTERS.keys()),
            limit=_limit(args, 20),
        ),
        "company_brain_configure_sync": lambda args: configure_company_brain_sync(
            _founder(args),
            enabled=bool(args.get("enabled", True)),
            sources=list(args.get("sources") or []),
            interval_minutes=_int_arg(args, "interval_minutes", 60, 5, 1440),
        ),
        "company_brain_run_sync": lambda args: run_company_brain_sync(_founder(args), force=bool(args.get("force", True))),
        "company_brain_maintain": lambda args: maintain_company_brain(_founder(args)),
        "company_brain_status": _status,
    }


def _tool_result(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, indent=2, sort_keys=True),
            }
        ],
        "structuredContent": payload,
        "isError": not bool(payload.get("ok", True)),
    }


def _resource_uri(founder_id: str | None = None) -> str:
    return f"astra://company-brain/{founder_id or _default_founder_id()}"


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC request or notification."""
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}
    if request_id is None:
        return None

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "serverInfo": SERVER_INFO,
                "capabilities": {"tools": {}, "resources": {}},
            }
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            dispatch = _dispatch_table().get(name)
            if dispatch is None:
                raise ValueError(f"Unknown company brain tool: {name}")
            result = _tool_result(dispatch(arguments))
        elif method == "resources/list":
            founder_id = str(params.get("founder_id") or _default_founder_id())
            result = {
                "resources": [{
                    "uri": _resource_uri(founder_id),
                    "name": "Astra Company Brain",
                    "description": "Founder-scoped source graph, canonical context, and sync state.",
                    "mimeType": "application/json",
                }]
            }
        elif method == "resources/read":
            uri = str(params.get("uri") or _resource_uri())
            founder_id = uri.rstrip("/").split("/")[-1] or _default_founder_id()
            result = {
                "contents": [{
                    "uri": _resource_uri(founder_id),
                    "mimeType": "application/json",
                    "text": json.dumps(_status({"founder_id": founder_id}), indent=2, sort_keys=True),
                }]
            }
        else:
            raise ValueError(f"Unsupported method: {method}")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def serve(stdin: Any = None, stdout: Any = None) -> None:
    """Run a newline-delimited JSON-RPC server over stdio."""
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    for line in input_stream:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        else:
            response = handle_request(request)
        if response is not None:
            output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
            output_stream.flush()


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
