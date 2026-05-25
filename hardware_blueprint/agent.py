"""
Blueprint conversation agent.
Multi-turn: gather requirements → generate full hardware design spec.
"""
import json
import logging
import os
import re
from dataclasses import dataclass, field

import openai

logger = logging.getLogger(__name__)

CLARIFY_SYSTEM = """You are Blueprint, an AI hardware design assistant. Your job is to understand exactly what hardware project the user wants to build.

Ask clarifying questions to gather:
1. Power source (battery type/size, USB, wall adapter, solar)
2. Control method (standalone/autonomous, smartphone app, web interface, physical buttons, voice)
3. Form factor (handheld, wearable, tabletop, wall-mounted, vehicle-mounted, breadboard prototype only)
4. Budget (rough USD range)
5. Skill level (beginner/intermediate/advanced — determines component complexity)
6. Any specific sensors, actuators, or connectivity requirements not yet mentioned

Output ONLY a JSON object:
{
  "has_enough_info": false,
  "questions": ["What power source will you use?", "How will you control it?"],
  "collected": {
    "project_name": "...",
    "description": "...",
    "power_source": null,
    "control_method": null,
    "form_factor": null,
    "budget_usd": null,
    "skill_level": null,
    "key_features": []
  }
}

When has_enough_info is true, populate all collected fields and ask no questions.
Output ONLY the JSON object."""

DESIGN_SYSTEM = """You are Blueprint, an AI hardware design assistant.
The user has described their hardware project. Generate a complete project overview and technical summary.

Output ONLY a JSON object:
{
  "project_name": "Short descriptive name",
  "tagline": "One-line description",
  "overview": "2-3 paragraph technical overview",
  "difficulty": "beginner / intermediate / advanced",
  "estimated_build_time_hours": 4,
  "estimated_total_cost_usd": 45,
  "microcontroller": "ESP32 / Arduino Uno / Raspberry Pi Zero / etc",
  "connectivity": ["WiFi", "Bluetooth"],
  "power_consumption_ma": 150,
  "key_challenges": ["challenge 1", "challenge 2"],
  "similar_projects": ["Instructables link pattern", "Hackaday category"],
  "firmware_language": "Arduino C++ / MicroPython / CircuitPython"
}

Output ONLY the JSON object."""


@dataclass
class ConversationState:
    messages: list = field(default_factory=list)
    collected: dict = field(default_factory=dict)
    phase: str = "clarify"  # clarify → designing → done
    design: dict = field(default_factory=dict)


class BlueprintAgent:
    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
    ):
        self.model = (
            model
            or os.getenv("BLUEPRINT_MODEL")
            or os.getenv("AGENT_MODEL_NAME", "moonshotai/Kimi-K2.5")
        )
        self._base_url = (
            base_url
            or os.getenv("BLUEPRINT_BASE_URL")
            or os.getenv("AGENT_MODEL_BASE_URL", "https://api.deepinfra.com/v1/openai")
        )
        self._api_key = (
            api_key
            or os.getenv("BLUEPRINT_API_KEY")
            or os.getenv("AGENT_MODEL_API_KEY", "dummy")
        )
        self._llm: openai.OpenAI | None = None

    def _get_llm(self) -> openai.OpenAI:
        if self._llm is None:
            self._llm = openai.OpenAI(base_url=self._base_url, api_key=self._api_key)
        return self._llm

    def _call(self, system: str, user: str, temperature: float = 0.1) -> str:
        resp = self._get_llm().chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        raw = resp.choices[0].message.content or ""
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw).rstrip("```").strip()
        return raw

    def _parse_json(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except Exception:
            pass
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except Exception:
                pass
        return {}

    def chat(self, state: ConversationState, user_message: str) -> dict:
        """
        Process one user turn. Returns:
        {
          "reply": "text to show user",
          "questions": [...],  # non-empty during clarification
          "ready_to_design": bool,
          "collected": {...}
        }
        """
        state.messages.append({"role": "user", "content": user_message})

        # Build conversation history for context
        history = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in state.messages
        )

        context = f"Conversation so far:\n{history}\n\nCurrent collected info: {json.dumps(state.collected)}"
        raw = self._call(CLARIFY_SYSTEM, context)
        parsed = self._parse_json(raw)

        state.collected = parsed.get("collected", state.collected) or state.collected
        questions = parsed.get("questions", [])
        has_enough = parsed.get("has_enough_info", False)

        if questions:
            reply = "\n".join(f"• {q}" for q in questions)
        elif has_enough:
            reply = "Got everything I need! Generating your hardware design now..."
        else:
            reply = "Tell me more about your project."

        state.messages.append({"role": "assistant", "content": reply})

        return {
            "reply": reply,
            "questions": questions,
            "ready_to_design": has_enough and not questions,
            "collected": state.collected,
        }

    def generate_info(self, spec: dict) -> dict:
        """Generate project overview/INFO section."""
        spec_text = "\n".join(f"{k}: {v}" for k, v in spec.items() if v)
        raw = self._call(DESIGN_SYSTEM, f"Project spec:\n{spec_text}", temperature=0.2)
        return self._parse_json(raw)

    def generate_full_design(self, spec: dict) -> dict:
        """Generate all 6 sections: INFO, BOM, WIRING, MECH, INSTRUCTIONS, PARTS."""
        from hardware_blueprint.generators.bom import generate_bom
        from hardware_blueprint.generators.wiring import generate_wiring
        from hardware_blueprint.generators.mechanical import generate_mechanical
        from hardware_blueprint.generators.instructions import generate_instructions
        from hardware_blueprint.generators.parts_lookup import enrich_bom_with_links

        llm = self._get_llm()

        logger.info("Generating INFO...")
        info = self.generate_info(spec)

        logger.info("Generating BOM...")
        bom_data = generate_bom(llm, self.model, spec)
        bom_items = bom_data.get("items", [])

        logger.info("Generating WIRING...")
        wiring = generate_wiring(llm, self.model, spec, bom_items)

        logger.info("Generating MECH...")
        mech = generate_mechanical(llm, self.model, spec, bom_items)

        logger.info("Generating INSTRUCTIONS...")
        instructions = generate_instructions(llm, self.model, spec, bom_items, wiring)

        logger.info("Enriching BOM with purchase links...")
        bom_items = enrich_bom_with_links(bom_items)

        return {
            "INFO": info,
            "BOM": {**bom_data, "items": bom_items},
            "WIRING": wiring,
            "MECH": mech,
            "INSTRUCTIONS": instructions,
            "PARTS": {
                "components": bom_items,
                "total_cost_usd": bom_data.get("total_cost_usd", 0),
            },
        }
