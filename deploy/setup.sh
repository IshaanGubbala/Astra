#!/bin/bash
# Run this once on a fresh Hetzner Ubuntu 24.04 box as root.
set -euo pipefail

# Docker
apt-get update && apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# certbot for TLS
apt-get install -y certbot

# Harden SSH
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl reload sshd

# App dir
mkdir -p /opt/astra
echo "Done. Now:"
echo "  1. scp or git clone the repo into /opt/astra"
echo "  2. Copy your .env file into /opt/astra/.env"
echo "  3. Run: cd /opt/astra && bash deploy/certbot.sh yourdomain.com"
echo "  4. Run: docker compose up -d"
