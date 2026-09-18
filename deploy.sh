#!/usr/bin/env bash
set -euo pipefail

# ===== Configuration =====
IMAGE=mstarman/shuttlebuilder:latest
# read -rp "Remote host (user@host): " REMOTE
# read -rp "Remote compose directory: " REMOTE_DIR

REMOTE=bwelns
REMOTE_DIR=/home/ubuntu/builder

ARCHIVE="deploy_$(date +%Y%m%d_%H%M%S).tar.gz"

echo "==> Building image..."
docker build -t ${IMAGE} .

echo "==> Saving image..."
docker save ${IMAGE} | gzip > "${ARCHIVE}"

echo "==> Uploading..."
scp "${ARCHIVE}" "${REMOTE}:/tmp/"

echo "==> Deploying..."

ssh "${REMOTE}" <<EOF
set -e

cd "${REMOTE_DIR}"

echo "Stopping containers..."
docker compose down

echo "Loading image..."
gunzip -c /tmp/${ARCHIVE} | docker load

rm /tmp/${ARCHIVE}

echo "Starting containers..."
docker compose up -d

echo "Cleaning unused images..."
docker image prune -f
EOF

rm "${ARCHIVE}"

echo
echo "Deployment completed successfully."