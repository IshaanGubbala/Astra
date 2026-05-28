"""
Sync LLM helper for content-generation tools.
Uses a fast 8B model on DeepInfra by default.
Pass model="claude" for high-quality creative output (landing pages, design docs) — also via DeepInfra.
"""
import re
from backend.config import settings

_FAST_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
_DI_BASE = "https://api.deepinfra.com/v1/openai"


def generate(prompt: str, max_tokens: int | None = None, json_mode: bool = False, model: str = "fast") -> str:
    """Call an LLM for content generation. Returns raw text."""
    import openai
    api_key = settings.deepinfra_api_key or settings.planner_model_api_key or settings.agent_model_api_key
    client = openai.OpenAI(base_url=_DI_BASE, api_key=api_key)
    selected_model = _FAST_MODEL
    kwargs: dict = dict(
        model=selected_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs, timeout=120.0)
    content = resp.choices[0].message.content or ""
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    return content
