#!/usr/bin/env bash
# Deploy ResumeFit AI API to Render (after `render login` and `render workspace set`).
set -euo pipefail

REPO="${REPO:-https://github.com/kakumanuharshithsubrahmanyam-wq/resumefit-ai}"
CORS="${CORS_ORIGINS:-https://frontend-liard-theta-0j80a7aaw6.vercel.app}"

render whoami
render services create \
  --confirm \
  --output json \
  --name resumefit-ai-api \
  --type web_service \
  --repo "$REPO" \
  --branch main \
  --runtime docker \
  --root-directory backend \
  --plan free \
  --health-check-path /api/v1/health \
  --env-var "ENVIRONMENT=production" \
  --env-var "DATABASE_URL=sqlite:////app/data/resumefit.db" \
  --env-var "MAX_UPLOAD_BYTES=5242880" \
  --env-var "RATE_LIMIT_REQUESTS_PER_MINUTE=120" \
  --env-var "AI_ENABLED=false" \
  --env-var "CORS_ORIGINS=$CORS"

echo "Set OPENAI_API_KEY in the Render dashboard and AI_ENABLED=true if you want AI recommendations."
