#!/bin/bash
# Usage: bash deploy/certbot.sh astracreates.com api.astracreates.com www.astracreates.com
set -euo pipefail
PRIMARY_DOMAIN=${1:?Usage: certbot.sh <primary-domain> [extra-domain ...]}
shift || true

DOMAIN_ARGS=(-d "$PRIMARY_DOMAIN")
for domain in "$@"; do
  DOMAIN_ARGS+=(-d "$domain")
done

certbot certonly --standalone "${DOMAIN_ARGS[@]}" --non-interactive --agree-tos -m admin@"$PRIMARY_DOMAIN"

mkdir -p deploy/certs
cp /etc/letsencrypt/live/"$PRIMARY_DOMAIN"/fullchain.pem deploy/certs/fullchain.pem
cp /etc/letsencrypt/live/"$PRIMARY_DOMAIN"/privkey.pem   deploy/certs/privkey.pem
chmod 600 deploy/certs/privkey.pem

echo "Certs copied to deploy/certs/. Run: docker compose up -d"
