#!/bin/bash
# Run from the Astra repo root after production env/DNS are configured.
set -euo pipefail

FOUNDER_ID=${FOUNDER_ID:-founder_prod}
STACK_ID=${STACK_ID:-idea_to_revenue}
BACKEND_URL=${BACKEND_URL:?Set BACKEND_URL, e.g. https://api.astracreates.com}
EXPECTED_BACKEND_IP=${EXPECTED_BACKEND_IP:-}

echo "== Astra production bootstrap =="
python -m backend.production_bootstrap \
  --founder-id "$FOUNDER_ID" \
  --stack-id "$STACK_ID" \
  --base-url "$BACKEND_URL" \
  ${EXPECTED_BACKEND_IP:+--expected-backend-ip "$EXPECTED_BACKEND_IP"}

echo "== Astra production network preflight =="
python -m backend.production_preflight \
  --base-url "$BACKEND_URL" \
  ${EXPECTED_BACKEND_IP:+--expected-backend-ip "$EXPECTED_BACKEND_IP"}

echo "== Astra launch readiness =="
python -m backend.launch_readiness \
  --founder-id "$FOUNDER_ID" \
  --stack-id "$STACK_ID" \
  --base-url "$BACKEND_URL" \
  --report-id latest

echo "== Astra final production launch proof =="
python -m backend.production_launch \
  --founder-id "$FOUNDER_ID" \
  --stack-id "$STACK_ID" \
  --base-url "$BACKEND_URL" \
  --live-connectors \
  --seed-env-connectors
