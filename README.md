# ResumeFit AI

Production-minded web application for comparing a resume to a job description, identifying skill gaps, evaluating experience, and generating improvement plans.

This repository is a monorepo with separate **frontend** and **backend** applications. The current phase includes a responsive SaaS UI, PDF/DOCX resume parsing, and frontend-backend integration. Skill matching and improvement plans are not implemented yet.

## Tech stack

| Layer | Technologies |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy (SQLite) |
| Parsing | PyMuPDF (PDF), python-docx (DOCX) |
| Matching (later) | scikit-learn |
| Tests | pytest (backend), Vitest (frontend API client) |

## Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) — production env vars, hosting layout, health checks, troubleshooting
- [PRIVACY.md](./PRIVACY.md) — uploads, AI processing, saved history, limitations

## Prerequisites

- **Node.js** 20+ and npm
- **Python** 3.11+

## Quick start

### 1. Environment variables

Copy the example file at the repo root and adjust if needed:

```bash
cp .env.example .env
```

You can also copy `.env` into `backend/` so FastAPI settings load automatically, or export variables in your shell.

| Variable | Purpose |
| --- | --- |
| `BACKEND_HOST` | Uvicorn bind host (default `127.0.0.1`) |
| `BACKEND_PORT` | Uvicorn port (default `8000`) |
| `DATABASE_URL` | SQLAlchemy URL (default SQLite under `backend/data/`) |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `VITE_API_BASE_URL` | Frontend API base URL (used at build/dev time) |
| `MAX_UPLOAD_BYTES` | Backend resume upload limit (default 5 MB) |
| `VITE_MAX_UPLOAD_BYTES` | Frontend client-side upload limit (should match backend) |

For local development, create `frontend/.env`:

```bash
echo 'VITE_API_BASE_URL=http://127.0.0.1:8000' > frontend/.env
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Use **Analyze** to upload a resume and parse it against job details.

### Resume parsing API

`POST /api/v1/resumes/parse` (multipart form)

| Field | Required | Description |
| --- | --- | --- |
| `file` | yes | PDF or DOCX resume (max 5 MB by default) |
| `job_title` | yes | Target role title |
| `job_description` | yes | Role description text |
| `company_name` | no | Optional company name |

Successful responses return extracted resume text and counts in `data`, plus echoed job metadata in `meta`. Uploaded files are processed in memory and are not persisted by default.

### Resume analysis API

`POST /api/v1/analysis/run` (JSON)

| Field | Required | Description |
| --- | --- | --- |
| `resume_text` | yes | Parsed resume plain text |
| `job_title` | yes | Target role title |
| `job_description` | yes | Role description |
| `company_name` | no | Optional company |
| `request_ai_recommendations` | no | Request LLM suggestions (default false) |
| `ai_consent` | conditional | Must be true when requesting AI processing |
| `save_to_history` | no | Persist structured results for this browser session |
| `resume_filename` | no | Optional filename metadata for saved history rows |

Returns deterministic requirement findings, weighted alignment scores, and optional AI recommendations. AI output never overrides deterministic classifications or scores. If the LLM is unavailable, the API falls back to deterministic recommendation templates.

### PDF export

- `POST /api/v1/analysis/export/pdf` — export the current structured analysis payload
- `GET /api/v1/analysis/{record_id}/export/pdf` — export a saved history record

Reports include scores, findings, evidence snippets, and recommendations. They exclude API secrets and raw uploaded files.

### Analysis history (browser session)

History is scoped to a private `X-Analysis-Session-Id` header (stored in browser `sessionStorage`). This is **not** user authentication—anyone with the session ID could access saved rows on the same backend instance.

| Endpoint | Description |
| --- | --- |
| `GET /api/v1/history` | List saved analyses for the session |
| `GET /api/v1/history/{id}` | Reopen a saved analysis |
| `DELETE /api/v1/history/{id}` | Delete one saved analysis |
| `DELETE /api/v1/history` | Clear all saved analyses for the session |

Stored records include structured scores/findings/recommendations and optional filename metadata—not raw resume files or full job descriptions by default beyond what is embedded in extracted requirement source snippets inside the analysis JSON.

## Development commands

### Backend

```bash
cd backend
source .venv/bin/activate
pytest
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev          # development server
npm run build        # production build
npm run test         # Vitest
npm run lint         # oxlint
```

## API conventions

### Successful responses

All successful JSON responses use this envelope:

```json
{
  "success": true,
  "data": { },
  "meta": null
}
```

### Errors

Errors return an appropriate HTTP status and:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Human-readable summary",
    "details": { }
  }
}
```

Validation failures use code `validation_error` (HTTP 422). Unhandled server errors use `internal_error` (HTTP 500).

## Project layout

```
.
├── backend/
│   ├── app/
│   │   ├── api/           # Routers and route modules
│   │   ├── exceptions/    # Global exception handlers
│   │   ├── schemas/       # Pydantic models (API envelope)
│   │   ├── services/      # Resume parsing and domain logic
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # UI + shadcn components
│   │   ├── lib/           # API client and utilities
│   │   └── types/
│   └── package.json
├── .env.example
└── README.md
```

## Security notes

- Do not commit `.env`, API keys, or uploaded resumes.
- Resume uploads and generated artifacts are ignored via `.gitignore`.
- AI integration is planned for a later phase.

## License

Private / unlicensed unless otherwise specified by the project owners.
