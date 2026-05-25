"""
Assembly instructions generator.
Step-by-step build guide with testing checkpoints.
"""
import json
import re


INSTRUCTIONS_SYSTEM = """You are a hardware assembly instructor. Generate clear step-by-step build instructions.

Output ONLY a JSON object:
{
  "tools_needed": ["soldering iron", "multimeter", "wire strippers", "screwdriver"],
  "phases": [
    {
      "phase": "1. Component Preparation",
      "steps": [
        "Inspect all components against the BOM. Check for bent pins.",
        "Flash the microcontroller with test firmware before assembly.",
        "Test each sensor individually with a breadboard before final assembly."
      ]
    },
    {
      "phase": "2. Power Circuit",
      "steps": ["Connect 5V rail...", "Verify voltage with multimeter before connecting MCU..."]
    },
    {
      "phase": "3. Sensor Connections",
      "steps": ["Wire HC-SR04 TRIG to GPIO4...", "Wire HC-SR04 ECHO to GPIO5 through voltage divider..."]
    },
    {
      "phase": "4. Testing & Validation",
      "steps": ["Power on and check for smoke/heat...", "Run diagnostic sketch...", "Verify sensor readings..."]
    },
    {
      "phase": "5. Enclosure Assembly",
      "steps": ["Mount PCB with M3 standoffs...", "Route cables..."]
    }
  ],
  "testing_checkpoints": [
    {"after": "power circuit", "test": "measure voltage at all rails with multimeter"},
    {"after": "full assembly", "test": "run provided diagnostic code"}
  ],
  "common_mistakes": [
    "Reversed polarity on electrolytic capacitors",
    "HC-SR04 runs on 5V but outputs 5V — needs level shifter for 3.3V MCU echo pin"
  ],
  "code_snippet": "minimal Arduino/MicroPython starter code to verify everything works"
}

Output ONLY the JSON object."""


def generate_instructions(llm_client, model: str, project_spec: dict, bom_items: list, wiring: dict) -> dict:
    """Generate assembly instructions."""
    context = _build_context(project_spec, bom_items, wiring)

    resp = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": INSTRUCTIONS_SYSTEM},
            {"role": "user", "content": f"Generate assembly instructions for:\n{context}"},
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


def _build_context(spec: dict, bom_items: list, wiring: dict) -> str:
    lines = [
        f"Project: {spec.get('project_name', 'Hardware Project')}",
        f"Description: {spec.get('description', '')}",
        f"Skill level: {spec.get('skill_level', 'intermediate')}",
    ]
    if bom_items:
        lines.append(f"Components: {', '.join(item.get('component', '') for item in bom_items)}")
    if wiring.get("connections"):
        conn_summary = [f"{c['from_component']} {c['from_pin']} → {c['to_component']} {c['to_pin']}"
                        for c in wiring["connections"][:10]]
        lines.append(f"Key connections: {'; '.join(conn_summary)}")
    if wiring.get("notes"):
        lines.append(f"Wiring notes: {'; '.join(wiring['notes'])}")
    return "\n".join(lines)
