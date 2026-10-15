# Privacy & Data Handling — ResumeFit AI

## Resume uploads

- PDF/DOCX uploads are processed **in memory** for parsing and analysis.
- Uploaded files are **not written to disk** by default.
- Application logs do not intentionally record resume or job description bodies.

## Analysis processing

- Deterministic analysis runs on the backend using extracted text supplied in API requests.
- Optional AI recommendations require explicit `ai_consent=true` and send truncated resume/job excerpts to the configured provider (OpenAI when configured).
- AI output does not override deterministic scores or classifications.

## Saved history (optional)

When `save_to_history=true`:

- Structured analysis results (scores, findings, recommendations, truncated evidence snippets, requirement source lines) are stored in SQLite.
- Raw resume files are **not** stored.
- Full job descriptions are **not** stored as a dedicated field; requirement `source_text` excerpts from the job description may appear inside the saved JSON.
- Records are associated with a browser session header (`X-Analysis-Session-Id`), **not** a verified user account.

## User controls

- Opt in/out of saving each analysis.
- Delete individual history entries or clear all history for the current session via the History UI/API.

## What this app does not provide

- No enterprise-grade authentication or multi-tenant isolation.
- No guarantee that session IDs cannot be guessed if exposed.
- No HIPAA/SOC2 compliance claims.

Use TLS, network controls, and authenticated gateways before exposing sensitive HR data in production.
