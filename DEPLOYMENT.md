# Budget Darpan deployment guide

This guide deploys the release candidate as three services:

```text
Vercel: React frontend
       ↓ HTTPS
Render: Django API ── PostgreSQL
       ↓ signed verification exchange
Render: independent mock identity provider
```

The committed files contain no production credentials. Never commit `.env`, PEM files, database files, uploaded documents, Chroma data, or API keys.

## 1. Prepare security values locally

From the repository root, generate ignored local secrets and an RSA key pair:

```powershell
python scripts/bootstrap_local_security.py
```

Keep these values ready for the hosting dashboards:

- `backend/.env`: `SECRET_KEY`, `CITIZEN_HASH_SECRET`, and `MOCK_IDENTITY_CLIENT_SECRET`
- `mock-identity-server/.env`: `DJANGO_SECRET_KEY`
- `mock-identity-server/keys/private.pem`: `IDENTITY_PRIVATE_KEY`
- `mock-identity-server/keys/public.pem`: `MOCK_IDENTITY_PUBLIC_KEY`

`IDENTITY_CLIENT_SECRET` on the identity service must exactly equal `MOCK_IDENTITY_CLIENT_SECRET` on the API. Paste PEM values only into secret environment fields. The settings also accept a single line with each newline represented as `\n`.

## 2. Create PostgreSQL

Create a PostgreSQL database on Neon, Render, Railway, or another managed provider. Copy its connection string into the API's `DATABASE_URL` secret. Use the provider's pooled connection string when it offers one.

Do not use SQLite for the hosted release: free web-service filesystems are usually ephemeral and multiple workers must share the same database.

## 3. Deploy both Render services

1. In Render, choose **New → Blueprint** and connect `karanbuildss/karan-rag`.
2. Select the root `render.yaml`.
3. Supply every value marked `sync: false`.

API values:

```text
SECRET_KEY=<generated backend secret>
DATABASE_URL=<PostgreSQL connection string>
PUBLIC_API_BASE_URL=https://budget-darpan-api.onrender.com
CORS_ALLOWED_ORIGINS=https://YOUR-FRONTEND.vercel.app
CSRF_TRUSTED_ORIGINS=https://YOUR-FRONTEND.vercel.app
SESSION_COOKIE_SAMESITE=None
CSRF_COOKIE_SAMESITE=None
MOCK_IDENTITY_SERVER_URL=https://budget-darpan-identity.onrender.com
MOCK_IDENTITY_CLIENT_SECRET=<shared generated client secret>
MOCK_IDENTITY_PUBLIC_KEY=<public.pem contents>
CITIZEN_HASH_SECRET=<generated citizen HMAC secret>
```

Identity-service values:

```text
DJANGO_SECRET_KEY=<generated identity Django secret>
CORS_ALLOWED_ORIGIN=https://YOUR-FRONTEND.vercel.app
IDENTITY_CLIENT_SECRET=<same shared client secret>
IDENTITY_PRIVATE_KEY=<private.pem contents>
DEMO_OTP=<six-digit demonstration code>
```

If Render changes either service name because the preferred name is unavailable, update `PUBLIC_API_BASE_URL` and `MOCK_IDENTITY_SERVER_URL` to the actual HTTPS URLs.

The API start command runs migrations, idempotently seeds the documented showcase data, evaluates anomaly rules, and starts Gunicorn. Reviewed structured facts are imported only when their supporting local source corpus is present. It does not ingest ignored private PDFs or publish reviewed facts whose supporting files are absent.

The hosted API uses secure `SameSite=None` cookies because Vercel and Render have different origins. The mock identity service intentionally runs one worker because its short-lived demonstration challenges are stored in memory; this avoids a confirmation request reaching a different worker.

Verify:

```text
https://YOUR-API.onrender.com/api/v1/health/
https://YOUR-IDENTITY.onrender.com/api/v1/health/
https://YOUR-API.onrender.com/api/docs/
```

## 4. Deploy the frontend on Vercel

1. Import `karanbuildss/karan-rag` into Vercel.
2. Set **Root Directory** to `frontend`.
3. Keep framework preset **Vite**, build command `npm run build`, and output directory `dist`.
4. Add these environment variables:

```text
VITE_API_URL=https://YOUR-API.onrender.com/api/v1
VITE_MOCK_IDENTITY_URL=https://YOUR-IDENTITY.onrender.com/api/v1
VITE_DEFAULT_LANGUAGE=en
VITE_DEMO_PROJECT_ID=e4d7eeb5-50f8-4a67-9c44-477d121f765d
VITE_ENABLE_VOICE=true
VITE_ENABLE_MOCK_VERIFICATION=true
```

5. Deploy, copy the final Vercel URL, and replace the temporary frontend URL in the Render CORS settings with that exact origin. Do not add a trailing slash.

`frontend/vercel.json` preserves React routes such as `/projects/:id`, `/documents/:id`, and `/investigator` when opened directly.

## 5. Enable hosted RAG deliberately

The structured investigator, citations, anomaly explanations, and lexical evidence fallback work without cloud generation. Full vector retrieval and generated answers additionally require an Ollama-compatible endpoint reachable from Render:

```text
OLLAMA_BASE_URL=https://YOUR-OLLAMA-ENDPOINT
OLLAMA_CHAT_MODEL=qwen2.5:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text-v2-moe
INVESTIGATOR_ENABLE_GENERATION=True
```

For Pinecone, add these API secrets only in Render—not Vercel or GitHub:

```text
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=<new secret key>
PINECONE_INDEX=budget-darpan
PINECONE_NAMESPACE=public-budget-documents
```

Then run from a Render Shell after Ollama is reachable:

```bash
python backend/manage.py index_project_evidence --all-projects
```

Pinecone stores vectors; it does not replace this project's embedding model or chat model. A local Ollama process on a teammate's laptop is not reachable by hosted Render services unless it is separately and securely exposed.

## 6. Hosted-document boundary

The repository intentionally excludes downloaded government PDFs and runtime uploads. The deployed synthetic reference document is generated on demand and remains visibly marked synthetic. To serve the full official document library reliably, add S3-compatible object storage and ingest the official corpus from a protected operator workflow. Until then, official landing-page links and reviewed page facts remain available, but ignored local PDF files are not deployed.

## 7. Final smoke test

1. Open the Vercel URL and switch English/Nepali.
2. Open project discovery, comparison, map, anomalies, and source library.
3. Open the synthetic complete-flow project and its generated PDF citation.
4. Ask one English, Nepali, and Romanized Nepali question.
5. Register, match the fictional identity, confirm the demo OTP, and submit feedback.
6. Confirm a second submission updates or rejects the duplicate instead of creating another rating.
7. Open a deep link in a new tab to confirm the Vercel rewrite works.

The mock provider demonstrates the control boundary only. It is not Nagarik App and must never be presented as official identity verification.
