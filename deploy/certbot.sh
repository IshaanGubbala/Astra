#!/bin/bash
# Usage: bash deploy/certbot.sh yourdomain.com
set -euo pipefail
DOMAIN=${1:?Usage: certbot.sh <domain>}

certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos -m admin@"$DOMAIN"

mkdir -p deploy/certs
cp /etc/letsencrypt/live/"$DOMAIN"/fullchain.pem deploy/certs/fullchain.pem
cp /etc/letsencrypt/live/"$DOMAIN"/privkey.pem   deploy/certs/privkey.pem
chmod 600 deploy/certs/privkey.pem

echo "Certs copied to deploy/certs/. Run: docker compose up -d"
