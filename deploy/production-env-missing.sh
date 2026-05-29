#!/bin/bash
# Print missing production .env keys as KEY= placeholders without exposing secrets.
set -euo pipefail

ENV_FILE=${ENV_FILE:-.env}
python -m backend.production_env --env-file "$ENV_FILE" --print-missing-template
