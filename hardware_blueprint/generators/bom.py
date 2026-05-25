"""
Bill of Materials generator.
Produces structured component lists with real part names, quantities, costs.
"""
import json
import re
from typing import Any


BOM_SYSTEM = """You are a hardware BOM specialist. Generate a Bill of Materials for the described hardware project.

Output ONLY a JSON array. Each item:
{
  "component": "exact component name",
  "part_number": "common part number or model (e.g. ESP32-WROOM-32, HC-SR04, L298N)",
  "quantity": 1,
  "unit_cost_usd": 3.50,
  "description": "one-line purpose",
  "where_to_buy": "Amazon/AliExpress/Mouser/Digikey/Adafruit"
}

Rules:
- Use real, purchasable components available in 2024
- Prefer common maker components (Arduino, ESP32, Raspberry Pi, off-shelf sensors)
- Include ALL required components: MCU, power, sensors, actuators, passives, connectors, enclosure
- Estimate realistic costs (not retail markup)
- Output ONLY the JSON array, nothing else"""


def generate_bom(llm_client, model: str, project_spec: dict) -> dict:
    """Generate BOM from project specification."""
    spec_text = _spec_to_text(project_spec)

    resp = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": BOM_SYSTEM},
            {"role": "user", "content": f"Generate BOM for:\n{spec_text}"},
        ],
        temperature=0.1,
    )
    raw = resp.choices[0].message.content or "[]"
    raw = re.sub(r"^```(?:json)?\s*", "", raw).rstrip("```").strip()

    try:
        items = json.loads(raw)
    except Exception:
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end > start:
            try:
                items = json.loads(raw[start:end + 1])
            except Exception:
                items = []
        else:
            items = []

    total = sum(item.get("unit_cost_usd", 0) * item.get("quantity", 1) for item in items)
    return {
        "items": items,
        "total_cost_usd": round(total, 2),
        "item_count": len(items),
    }


def _spec_to_text(spec: dict) -> str:
    lines = [f"Project: {spec.get('project_name', 'Hardware Project')}"]
    lines.append(f"Description: {spec.get('description', '')}")
    if spec.get("power_source"):
        lines.append(f"Power: {spec['power_source']}")
    if spec.get("control_method"):
        lines.append(f"Control: {spec['control_method']}")
    if spec.get("form_factor"):
        lines.append(f"Form factor: {spec['form_factor']}")
    if spec.get("budget_usd"):
        lines.append(f"Budget: ${spec['budget_usd']}")
    if spec.get("skill_level"):
        lines.append(f"Skill level: {spec['skill_level']}")
    if spec.get("key_features"):
        lines.append(f"Key features: {', '.join(spec['key_features'])}")
    return "\n".join(lines)
