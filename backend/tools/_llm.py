"""
Sync LLM helper for content-generation tools.
Uses a fast 8B model on DeepInfra — keeps tool calls snappy.
"""
import re
from backend.config import settings

# Fast model for tool-level generation (legal docs, social copy, etc.)
_FAST_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
_DI_BASE = "https://api.deepinfra.com/v1/openai"


def generate(prompt: str, max_tokens: int | None = 2048, json_mode: bool = False) -> str:
    """Call a fast LLM for content generation. Returns raw text."""
    import openai
    from backend.config import settings as s
    api_key = s.deepinfra_api_key or s.planner_model_api_key or s.agent_model_api_key
    client = openai.OpenAI(base_url=_DI_BASE, api_key=api_key)
    kwargs = dict(
        model=_FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs, timeout=30.0)
    content = resp.choices[0].message.content or ""
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    return content
