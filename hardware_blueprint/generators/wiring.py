"""
Wiring diagram generator.
Produces textual + ASCII wiring descriptions and connection tables.
"""
import json
import re


WIRING_SYSTEM = """You are an electronics wiring specialist. Generate wiring instructions for a hardware project.

Output ONLY a JSON object:
{
  "connections": [
    {
      "from_component": "ESP32",
      "from_pin": "GPIO 4",
      "to_component": "HC-SR04",
      "to_pin": "TRIG",
      "wire_color": "yellow",
      "voltage": "3.3V",
      "signal_type": "digital output"
    }
  ],
  "power_rails": [
    {
      "voltage": "5V",
      "components": ["HC-SR04 VCC", "L298N VCC"],
      "source": "USB or 5V regulator"
    }
  ],
  "ascii_diagram": "simple ASCII art showing major connections",
  "notes": ["important wiring notes", "e.g. add pull-up resistor on pin X"]
}

Rules:
- List every wire connection explicitly
- Include all power and ground connections
- Use standard pin names for common components
- Flag any voltage level mismatches or level shifter requirements
- Output ONLY the JSON object"""


SCHEMATIC_SYSTEM = """You are an electronics specialist. Generate a readable ASCII schematic/block diagram.

Create an ASCII block diagram showing how components connect. Use boxes for components and lines/arrows for connections.
Keep it readable in a monospace terminal. Show power flow (VCC→component→GND).

Output ONLY the ASCII diagram as plain text (no JSON, no markdown fences)."""


def generate_wiring(llm_client, model: str, project_spec: dict, bom_items: list) -> dict:
    """Generate wiring diagram from spec + BOM."""
    spec_text = _build_context(project_spec, bom_items)

    resp = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": WIRING_SYSTEM},
            {"role": "user", "content": f"Generate wiring for:\n{spec_text}"},
        ],
        temperature=0.1,
    )
    raw = resp.choices[0].message.content or "{}"
    raw = re.sub(r"^```(?:json)?\s*", "", raw).rstrip("```").strip()

    try:
        data = json.loads(raw)
    except Exception:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            try:
                data = json.loads(raw[start:end + 1])
            except Exception:
                data = {}
        else:
            data = {}

    # Generate ASCII schematic separately for better quality
    ascii_resp = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SCHEMATIC_SYSTEM},
            {"role": "user", "content": f"Create block diagram for:\n{spec_text}"},
        ],
        temperature=0.2,
    )
    ascii_diagram = ascii_resp.choices[0].message.content or ""
    ascii_diagram = re.sub(r"^```\w*\s*", "", ascii_diagram).rstrip("```").strip()
    data["ascii_diagram"] = ascii_diagram

    return data


def _build_context(spec: dict, bom_items: list) -> str:
    lines = [f"Project: {spec.get('project_name', 'Hardware Project')}"]
    lines.append(f"Description: {spec.get('description', '')}")
    if spec.get("power_source"):
        lines.append(f"Power: {spec['power_source']}")
    if bom_items:
        component_names = [item.get("component", "") for item in bom_items if item.get("component")]
        lines.append(f"Components: {', '.join(component_names)}")
    return "\n".join(lines)
