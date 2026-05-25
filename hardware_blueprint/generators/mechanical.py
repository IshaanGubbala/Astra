"""
Mechanical design generator.
Produces enclosure specs, component layout, and dimension estimates.
"""
import json
import re


MECH_SYSTEM = """You are a hardware mechanical design specialist. Generate mechanical/physical design specs.

Output ONLY a JSON object:
{
  "enclosure": {
    "type": "3D printed box / off-shelf project box / PCB only / custom",
    "dimensions_mm": {"width": 100, "height": 60, "depth": 30},
    "material": "PLA / ABS / aluminum / acrylic",
    "mounting": "wall-mount / handheld / tabletop / wearable"
  },
  "component_layout": [
    {
      "component": "ESP32",
      "position": "center of PCB",
      "notes": "main controller, needs antenna clearance from edge"
    }
  ],
  "cutouts": [
    {"purpose": "USB port access", "size": "12x5mm", "location": "short side"},
    {"purpose": "sensor window", "size": "20x20mm", "location": "top face"}
  ],
  "pcb_notes": "single-layer perfboard OK / custom PCB recommended / use dev board",
  "assembly_difficulty": "beginner / intermediate / advanced",
  "estimated_build_time_hours": 3,
  "ascii_layout": "top-down ASCII view of component placement"
}

Output ONLY the JSON object."""


def generate_mechanical(llm_client, model: str, project_spec: dict, bom_items: list) -> dict:
    """Generate mechanical design from spec + BOM."""
    spec_text = _build_context(project_spec, bom_items)

    resp = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": MECH_SYSTEM},
            {"role": "user", "content": f"Generate mechanical design for:\n{spec_text}"},
        ],
        temperature=0.2,
    )
    raw = resp.choices[0].message.content or "{}"
    raw = re.sub(r"^```(?:json)?\s*", "", raw).rstrip("```").strip()

    try:
        return json.loads(raw)
    except Exception:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except Exception:
                pass
    return {}


def _build_context(spec: dict, bom_items: list) -> str:
    lines = [
        f"Project: {spec.get('project_name', 'Hardware Project')}",
        f"Description: {spec.get('description', '')}",
    ]
    if spec.get("form_factor"):
        lines.append(f"Form factor: {spec['form_factor']}")
    if spec.get("skill_level"):
        lines.append(f"Skill level: {spec['skill_level']}")
    if bom_items:
        names = [item.get("component", "") for item in bom_items]
        lines.append(f"Components: {', '.join(names)}")
    return "\n".join(lines)
