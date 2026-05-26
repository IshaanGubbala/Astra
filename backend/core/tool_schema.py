"""Build OpenAI-compatible function schemas from Python callables."""
import inspect
from typing import get_type_hints


_PY_TO_JSON = {
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    str: "string",
}


def build_tool_schema(name: str, fn) -> dict:
    """Return an OpenAI function-schema dict for *fn* named *name*."""
    try:
        sig = inspect.signature(fn)
    except (ValueError, TypeError):
        sig = None

    doc = (fn.__doc__ or "").strip()
    description = doc.split("\n")[0] if doc else name.replace("_", " ")

    properties: dict = {}
    required: list = []

    if sig:
        try:
            hints = get_type_hints(fn)
        except Exception:
            hints = {}

        for pname, param in sig.parameters.items():
            if pname in ("self", "cls"):
                continue
            hint = hints.get(pname)
            json_type = _PY_TO_JSON.get(hint, "string")
            prop: dict = {"type": json_type}
            if json_type == "array":
                prop["items"] = {"type": "string"}
            properties[pname] = prop
            if param.default is inspect.Parameter.empty:
                required.append(pname)

    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }
