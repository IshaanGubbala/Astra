"""
Sync LLM helper for content-generation tools.

Models:
  "fast"    → DeepSeek-V4-Flash   (default, general purpose)
  "large"   → gpt-oss-120b        (small input, high output — docs, copy)
  "instruct" → Llama-3.3-70B      (strict rule-following: HTML, design, sales)
  "image"   → FLUX-2-pro          (image generation)
"""
import re
from backend.config import settings

_FAST_MODEL = "deepseek-ai/DeepSeek-V4-Flash"
_LARGE_MODEL = "openai/gpt-oss-120b"
_INSTRUCT_MODEL = "meta-llama/Meta-Llama-3.3-70B-Instruct"
_IMAGE_MODEL = "black-forest-labs/FLUX-2-pro"
_PROMPT_MODEL = "openai/gpt-oss-120b"
_DI_BASE = "https://api.deepinfra.com/v1/openai"
_DI_IMAGE_BASE = "https://api.deepinfra.com/v1/inference"


def _api_key() -> str:
    return settings.deepinfra_api_key or settings.planner_model_api_key or settings.agent_model_api_key


def generate(prompt: str, max_tokens: int | None = None, json_mode: bool = False, model: str = "large") -> str:
    """Call an LLM for content generation. Returns raw text.
    model="fast"     → DeepSeek-V4-Flash (general)
    model="large"    → gpt-oss-120b (high-output docs/copy)
    model="instruct" → Llama-3.3-70B (strict rule-following: HTML, design constraints)
    """
    import openai
    client = openai.OpenAI(base_url=_DI_BASE, api_key=_api_key())
    if model == "large":
        selected = _LARGE_MODEL
    elif model == "instruct":
        selected = _INSTRUCT_MODEL
    else:
        selected = _FAST_MODEL
    kwargs: dict = dict(
        model=selected,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs, timeout=120.0)
    content = resp.choices[0].message.content or ""
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()


_IMAGE_COST = 0.03          # FLUX-2-pro cost per image in USD
_IMAGE_MONTHLY_BUDGET = 1.50  # per founder per month


def _check_image_budget(founder_id: str) -> tuple[bool, float]:
    """Returns (allowed, remaining_budget). Uses Redis for tracking."""
    try:
        import redis, calendar, datetime
        from backend.config import settings
        r = redis.from_url(settings.redis_url, decode_responses=True)
        now = datetime.datetime.utcnow()
        key = f"img_spend:{founder_id}:{now.year}:{now.month}"
        spent = float(r.get(key) or 0)
        remaining = _IMAGE_MONTHLY_BUDGET - spent
        return remaining >= _IMAGE_COST, remaining
    except Exception:
        return True, _IMAGE_MONTHLY_BUDGET  # fail open if Redis down


def _record_image_spend(founder_id: str) -> None:
    try:
        import redis, datetime
        from backend.config import settings
        r = redis.from_url(settings.redis_url, decode_responses=True)
        now = datetime.datetime.utcnow()
        key = f"img_spend:{founder_id}:{now.year}:{now.month}"
        r.incrbyfloat(key, _IMAGE_COST)
        # expire after 35 days
        if not r.ttl(key) or r.ttl(key) < 0:
            r.expire(key, 35 * 86400)
    except Exception:
        pass


def generate_image(description: str, width: int = 1024, height: int = 1024, founder_id: str = "") -> dict:
    """Generate an ad image using Janus-Pro-7B.
    Uses Llama-3.3-70B to write an optimized image prompt, then calls Janus.
    Returns: {prompt, url, base64, model}
    """
    import openai, requests

    # Check monthly budget
    if founder_id:
        allowed, remaining = _check_image_budget(founder_id)
        if not allowed:
            return {"error": f"Monthly image budget exhausted (${_IMAGE_MONTHLY_BUDGET:.2f}/month). Resets next month.", "model": _IMAGE_MODEL}

    # Step 1: gpt-oss-120b writes the FLUX image prompt
    client = openai.OpenAI(base_url=_DI_BASE, api_key=_api_key())
    prompt_resp = client.chat.completions.create(
        model=_PROMPT_MODEL,
        messages=[
            {"role": "system", "content": (
                "You are a creative director at a top-tier advertising agency. "
                "Your job is to write image generation prompts for FLUX-2-pro diffusion model.\n\n"
                "FLUX responds best to SHORT, DENSE prompts — 40 to 80 words maximum. "
                "Long prompts degrade quality. Be precise, not verbose.\n\n"
                "Great FLUX ad prompts have:\n"
                "  • A single strong visual anchor (one person, one product, one moment)\n"
                "  • Specific lighting in 3-5 words ('soft morning window light', 'dramatic side rim')\n"
                "  • Emotional tone in 2-3 words ('quiet confidence', 'raw joy')\n"
                "  • Large open area of negative space for text — say exactly where (top third, left half)\n"
                "  • End with: 'editorial advertising photography, 35mm, magazine quality'\n\n"
                "DO NOT include: brand names, logos, text, words, watermarks, charts, multiple people unless essential.\n"
                "DO NOT use: 'photorealistic', 'ultra HD', 'masterpiece', 'beautiful' — these are filler.\n"
                "Output ONLY the prompt. No explanation. No quotes. No markdown."
            )},
            {"role": "user", "content": (
                f"Ad concept and brand context:\n{description}\n\n"
                "Write the FLUX-2-pro image prompt now. Keep it under 80 words."
            )},
        ],
        max_tokens=150,
        temperature=0.75,
        timeout=30.0,
    )
    image_prompt = (prompt_resp.choices[0].message.content or description).strip()

    # Step 2: Janus generates the image
    try:
        headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
        resp = requests.post(
            f"{_DI_IMAGE_BASE}/{_IMAGE_MODEL}",
            headers=headers,
            json={"prompt": image_prompt, "width": width, "height": height, "num_images": 1},
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
        # FLUX-2-pro returns image_url; schnell/dev return images array with base64
        url = data.get("image_url")
        images = data.get("images") or data.get("output") or []
        img = images[0] if images else None
        b64 = None
        if img:
            b64 = img.get("image") if isinstance(img, dict) else img
            if not url and isinstance(img, dict):
                url = img.get("url")
        if founder_id and (url or b64):
            _record_image_spend(founder_id)
        return {
            "prompt": image_prompt,
            "url": url,
            "base64": b64,
            "model": _IMAGE_MODEL,
            "width": width,
            "height": height,
        }
    except Exception as e:
        return {"prompt": image_prompt, "error": str(e), "model": _IMAGE_MODEL}
