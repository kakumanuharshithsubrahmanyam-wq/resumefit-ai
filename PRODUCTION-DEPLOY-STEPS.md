# Production deployment — remaining steps

## Current status

| Component | URL | Verified |
| --- | --- | --- |
| Frontend (Vercel) | https://frontend-liard-theta-0j80a7aaw6.vercel.app | Landing page HTTP 200 |
| Backend (API) | **Not deployed** | Blocked: complete `render login` (device authorization in browser) |

The Vercel build currently embeds `http://127.0.0.1:8000` because `VITE_API_BASE_URL` was not set at build time. **Redeploy the frontend after the backend URL exists.**

## Step A — Authenticate Render

```bash
render login
render workspace set   # choose your workspace
```

## Step B — Deploy backend from this repository

1. Push this repo to GitHub (or connect the existing remote).
2. In [Render Dashboard](https://dashboard.render.com/) → **Blueprints** → **New Blueprint Instance**.
3. Connect the GitHub repository and use the root `render.yaml` (push latest `main` first — includes free-tier SQLite notes and default CORS).
4. Confirm **`CORS_ORIGINS`** is `https://frontend-liard-theta-0j80a7aaw6.vercel.app` (already set in `render.yaml`; override in dashboard if your Vercel URL differs).
5. Optional: set `AI_ENABLED=true` and add **`OPENAI_API_KEY`** as a secret if you want AI recommendations.
6. Wait for deploy; copy the public service URL (example shape: `https://resumefit-ai-api.onrender.com`).

Health check: `GET https://<your-backend>/api/v1/health` → `database: ok`.

## Step C — Point Vercel at the backend

From `frontend/`:

```bash
vercel env add VITE_API_BASE_URL production
# paste https://<your-backend-host>  (no trailing slash)

vercel deploy --prod --yes
```

Optional: add `VITE_MAX_UPLOAD_BYTES=5242880` in Vercel project settings.

## Step D — Re-run production verification

Use synthetic resumes only (no personal data). Confirm parse, analysis, PDF export, history, CORS, and error messages on the public URLs.

## Railway alternative

If you prefer Railway, upgrade the workspace plan (trial expired on this account), then:

```bash
cd backend
railway init --name resumefit-ai-api
railway variables set ENVIRONMENT=production DATABASE_URL=sqlite:////app/data/resumefit.db ...
railway up
railway domain
```

Mount a volume at `/app/data` for SQLite history persistence.
