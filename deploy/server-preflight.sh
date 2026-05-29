#!/bin/bash
# Run on the production server from the Astra repo root.
set -euo pipefail

FOUNDER_ID=${FOUNDER_ID:-founder_prod}
STACK_ID=${STACK_ID:-idea_to_revenue}
BACKEND_URL=${BACKEND_URL:-https://api.astracreates.com}
EXPECTED_BACKEND_IP=${EXPECTED_BACKEND_IP:-167.235.151.204}
FRONTEND_URL=${FRONTEND_URL:-https://astracreates.com}

status=0

section() {
  printf '\n== %s ==\n' "$1"
}

section "Repository"
if [ -d .git ]; then
  echo "branch=$(git rev-parse --abbrev-ref HEAD)"
  echo "commit=$(git rev-parse --short HEAD)"
  if [ -n "$(git status --short)" ]; then
    echo "worktree=dirty"
  else
    echo "worktree=clean"
  fi
else
  echo "git=missing"
  status=1
fi

section "Environment presence"
python -m backend.production_env --env-file .env || status=1
echo "missing_env_placeholders_begin"
python -m backend.production_env --env-file .env --print-missing-template || true
echo "missing_env_placeholders_end"

section "Docker compose"
if docker compose ps >/tmp/astra-compose-ps 2>/tmp/astra-compose-err; then
  cat /tmp/astra-compose-ps
else
  cat /tmp/astra-compose-err
  status=1
fi

section "Local service endpoints"
for url in \
  "http://127.0.0.1:8000/health" \
  "http://127.0.0.1:8000/ready" \
  "http://127.0.0.1:8000/metrics" \
  "http://127.0.0.1:3000/"; do
  code=$(curl -sS -o /tmp/astra-preflight-body -w "%{http_code}" "$url" || true)
  echo "$url status=$code"
  if [ "$code" -lt 200 ] || [ "$code" -ge 400 ]; then
    status=1
  fi
done

section "Public DNS and API preflight"
python -m backend.production_preflight \
  --base-url "$BACKEND_URL" \
  --expected-backend-ip "$EXPECTED_BACKEND_IP" || status=1

section "Bootstrap summary"
python -m backend.production_bootstrap \
  --founder-id "$FOUNDER_ID" \
  --stack-id "$STACK_ID" \
  --base-url "$BACKEND_URL" \
  --expected-backend-ip "$EXPECTED_BACKEND_IP" || status=1

section "Next command"
echo "FOUNDER_ID=$FOUNDER_ID STACK_ID=$STACK_ID BACKEND_URL=$BACKEND_URL EXPECTED_BACKEND_IP=$EXPECTED_BACKEND_IP deploy/production-proof.sh"

exit "$status"
