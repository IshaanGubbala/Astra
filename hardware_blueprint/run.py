#!/usr/bin/env python3
"""
Start Blueprint dev server.
Usage:
  python -m hardware_blueprint.run
  # or from Astra root:
  python hardware_blueprint/run.py

Env vars:
  BLUEPRINT_MODEL      — LLM model name (default: reads from local MLX server)
  BLUEPRINT_BASE_URL   — OpenAI-compatible API base URL
  BLUEPRINT_API_KEY    — API key (default: dummy for local)
  BLUEPRINT_PORT       — Port (default: 8090)
"""
import os
import sys
from pathlib import Path

# Ensure Astra root is on path regardless of how this script is invoked
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env from Astra root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("BLUEPRINT_PORT", "8090"))
    print(f"\n  Blueprint running → http://localhost:{port}\n")
    uvicorn.run(
        "hardware_blueprint.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)],
    )
