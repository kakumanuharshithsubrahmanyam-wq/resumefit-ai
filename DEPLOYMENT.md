# Deployment Guide — ResumeFit AI

This document describes a production-compatible deployment layout. **Deployment was not executed from this repository session** because no target hosting credentials or domains were configured here. Use the steps below on your chosen platform.

## Recommended hosting arrangement

| Component | Suggested platform | Notes |
| --- | --- | --- |
| Frontend (static) | Vercel, Netlify, Cloudflare Pages, or S3 + CloudFront | Build with `npm run build`; serve `frontend/dist` |
| Backend (API) | Render, Railway, Fly.io, AWS ECS/Fargate, or a VPS | Run Uvicorn/Gunicorn; persist SQLite volume or use managed Postgres |
| Database | SQLite file volume (small) or Postgres (multi-instance) | Required only for optional analysis history |

The frontend must call the backend using a **production API URL** (`VITE_API_BASE_URL`). The backend must allow the frontend origin in `CORS_ORIGINS`.

## Environment variables

### Backend (required)

| Variable | Example | Purpose |
| --- | --- | --- |
| `ENVIRONMENT` | `production` | Environment label returned by `/health` |
| `DATABASE_URL` | `sqlite:////data/resumefit.db` | SQLAlchemy URL (use persistent volume path in prod) |
| `CORS_ORIGINS` | `https://app.example.com` | Comma-separated allowed browser origins |
| `MAX_UPLOAD_BYTES` | `5242880` | Upload size limit (5 MB default) |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `120` | Per-IP limit (single-instance in-memory) |

### Backend (optional AI)

| Variable | Purpose |
| --- | --- |
| `AI_ENABLED` | Toggle AI recommendations |
| `OPENAI_API_KEY` | Server-side only; never expose to frontend |
| `OPENAI_MODEL` | Model name |
| `AI_TIMEOUT_SECONDS` | Provider timeout |
| `AI_MAX_INPUT_CHARS` | Truncation limit for provider payloads |

### Frontend (build-time)

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Backend public URL (required in production builds) |
| `VITE_MAX_UPLOAD_BYTES` | Client-side upload validation |

See `.env.example`, `backend/.env.example`, and `frontend/.env.production.example`.

## Backend production command

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

For multiple workers, prefer a shared database (Postgres) and an external rate limiter— the built-in limiter is **in-memory per instance**.

## Frontend production build

```bash
cd frontend
export VITE_API_BASE_URL=https://api.your-domain.example
npm ci
npm run build
```

Deploy the contents of `frontend/dist`.

## Health checks

- `GET /api/v1/health` should return `success: true` and `database: ok`.
- Configure your load balancer to use this endpoint.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Frontend shows network errors | Wrong `VITE_API_BASE_URL` or CORS | Rebuild frontend with correct API URL; set `CORS_ORIGINS` |
| History empty after redeploy | SQLite not on persistent volume | Mount `backend/data` or migrate to Postgres |
| AI recommendations always fallback | Missing/invalid `OPENAI_API_KEY` | Set key on backend only |
| 429 responses | Rate limit exceeded | Increase `RATE_LIMIT_REQUESTS_PER_MINUTE` or add gateway throttling |
| Upload fails with 413 | File exceeds `MAX_UPLOAD_BYTES` | Adjust limit consistently on frontend and backend |

## Docker (optional)

Example backend container start:

```bash
docker build -t resumefit-backend ./backend
docker run --env-file backend/.env -p 8000:8000 -v resumefit-data:/app/data resumefit-backend
```

A `backend/Dockerfile` is included for convenience.

## Security limitations (honest)

- There is **no user authentication**. History is scoped by browser session ID header, not verified identity.
- Session IDs are secrecy-based, not cryptographic auth.
- Do not expose the backend publicly without TLS and an API gateway/WAF for production traffic.
- Resume files are not stored by default; optional saved history stores structured analysis JSON with truncated evidence snippets and job requirement source lines.
