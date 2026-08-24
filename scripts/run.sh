#!/bin/bash
set -euo pipefail

# Decode base64 secrets from env into files
echo "$YT_TOKEN_B64" | base64 -d > /tmp/youtube_token.json
echo "$YT_CLIENT_SECRETS_B64" | base64 -d > /tmp/youtube_client_secret.json

# Sanity check
[ -s /tmp/youtube_token.json ] || { echo "YT_TOKEN_B64 missing"; exit 1; }
[ -s /tmp/youtube_client_secret.json ] || { echo "YT_CLIENT_SECRETS_B64 missing"; exit 1; }

# CONTENT_TYPE must be set by Railway cron (fact|song)
: "${CONTENT_TYPE:?CONTENT_TYPE env var required (fact|song)}"

echo "==> Running pipeline: CONTENT_TYPE=$CONTENT_TYPE"
cd /app
python -m src.main
