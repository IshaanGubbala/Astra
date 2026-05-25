"""
Blueprint.am clone — FastAPI backend.
Endpoints:
  POST /chat          — multi-turn conversation, returns questions or ready signal
  POST /design        — generate full design from collected spec
  GET  /              — serve frontend
"""
import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from hardware_blueprint.agent import BlueprintAgent, ConversationState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blueprint", description="AI Hardware Design Tool")

# In-memory session store (fine for single-user dev)
_sessions: dict[str, ConversationState] = {}
_agent = BlueprintAgent()


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class DesignRequest(BaseModel):
    session_id: str


@app.post("/chat")
async def chat(req: ChatRequest):
    """Multi-turn conversation to gather hardware project requirements."""
    session_id = req.session_id or uuid.uuid4().hex
    if session_id not in _sessions:
        _sessions[session_id] = ConversationState()

    state = _sessions[session_id]
    result = _agent.chat(state, req.message)

    return JSONResponse({
        "session_id": session_id,
        "reply": result["reply"],
        "questions": result["questions"],
        "ready_to_design": result["ready_to_design"],
        "collected": result["collected"],
    })


@app.post("/design")
async def design(req: DesignRequest):
    """Generate full hardware design (BOM, WIRING, MECH, INSTRUCTIONS, PARTS, INFO)."""
    state = _sessions.get(req.session_id)
    if not state:
        raise HTTPException(404, "Session not found. Start a conversation first.")

    spec = state.collected
    if not spec or not spec.get("description"):
        raise HTTPException(400, "Not enough information collected yet. Continue chatting.")

    logger.info("Generating full design for session %s: %s", req.session_id, spec.get("project_name"))
    design_result = _agent.generate_full_design(spec)

    # Enrich BOM with classification + images for schematic
    from hardware_blueprint.generators.component_classifier import (
        enrich_bom_with_classification, fetch_component_images
    )
    bom = design_result.get("BOM", {})
    items = bom.get("items", [])
    items = enrich_bom_with_classification(items)
    items = fetch_component_images(items)
    design_result["BOM"]["items"] = items
    design_result["PARTS"]["components"] = items

    # Build schematic graph: nodes + edges
    design_result["SCHEMATIC"] = _build_schematic(items, design_result.get("WIRING", {}))

    state.phase = "done"
    state.design = design_result

    return JSONResponse({"session_id": req.session_id, "design": design_result})


def _build_schematic(bom_items: list, wiring: dict) -> dict:
    """Convert BOM + wiring into Cytoscape.js-compatible nodes/edges."""
    from hardware_blueprint.generators.component_classifier import get_edge_color, is_edge_dashed

    nodes = []
    seen_ids: dict[str, str] = {}  # component name → node id

    for i, item in enumerate(bom_items):
        node_id = f"n{i}"
        name = item.get("component", f"Component {i}")
        seen_ids[name.lower()] = node_id
        nodes.append({
            "data": {
                "id": node_id,
                "label": name,
                "type": item.get("node_type", "MODULE"),
                "color": item.get("node_color", "#78909c"),
                "image": item.get("image_url"),
                "part_number": item.get("part_number", ""),
                "cost": item.get("unit_cost_usd", 0),
                "category": item.get("category", "Electrical"),
            }
        })

    edges = []
    connections = wiring.get("connections", [])
    for j, conn in enumerate(connections):
        from_name = (conn.get("from_component") or "").lower()
        to_name = (conn.get("to_component") or "").lower()
        signal = conn.get("signal_type", "DATA")

        # Fuzzy match node IDs
        from_id = _fuzzy_match(from_name, seen_ids)
        to_id = _fuzzy_match(to_name, seen_ids)
        if not from_id or not to_id or from_id == to_id:
            continue

        edges.append({
            "data": {
                "id": f"e{j}",
                "source": from_id,
                "target": to_id,
                "label": f"{conn.get('from_pin', '')} → {conn.get('to_pin', '')}",
                "signal": signal,
                "color": get_edge_color(signal),
                "dashed": is_edge_dashed(signal),
            }
        })

    return {"nodes": nodes, "edges": edges}


def _fuzzy_match(name: str, seen_ids: dict[str, str]) -> str | None:
    """Match component name to node id by substring."""
    if name in seen_ids:
        return seen_ids[name]
    for key, nid in seen_ids.items():
        if name in key or key in name:
            return nid
    # word-level match
    words = name.split()
    for word in words:
        if len(word) > 3:
            for key, nid in seen_ids.items():
                if word in key:
                    return nid
    return None


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    state = _sessions.get(session_id)
    if not state:
        raise HTTPException(404, "Session not found")
    return {
        "session_id": session_id,
        "phase": state.phase,
        "collected": state.collected,
        "messages": state.messages,
        "has_design": bool(state.design),
    }


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).parent / "frontend" / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text())
    return HTMLResponse("<h1>Blueprint API running. Frontend not found.</h1>")


@app.get("/health")
async def health():
    return {"status": "ok", "model": _agent.model, "base_url": _agent._base_url}
