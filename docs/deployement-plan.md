# Deployment (free tier, no card)

| Piece | Platform | URL |
|---|---|---|
| Frontend (Vite + React) | Vercel project `hdfc-mf-rag-chat`, root dir `frontend` | https://hdfc-mf-rag-chat.vercel.app |
| Backend (FastAPI + ChromaDB + fastembed) | Vercel project `hdfc-mf-rag-api`, root dir `.` | https://hdfc-mf-rag-api.vercel.app |
| LLM | Groq free tier (`GROQ_MODEL`, default `openai/gpt-oss-20b`) | |
| Daily data refresh | GitHub Actions ([ingest_cron.yml](../.github/workflows/ingest_cron.yml)) | commits `vectorstore/` + `db/metadata.db` to `main` |

```
User -> Vercel (React) -> Vercel Python function (FastAPI) -> Groq
                               ^ vectorstore/ + db/ shipped in the repo
```

## How the backend runs on Vercel

- Entrypoint: `[tool.vercel] entrypoint` in [pyproject.toml](../pyproject.toml) (`src.api.main:app`). The `dependencies` list there is the runtime set; `requirements.txt` is for local dev and the ingest workflow. Keep them in sync.
- Vercel's filesystem is read-only except `/tmp`. [src/utils/config.py](../src/utils/config.py) copies `vectorstore/` and `db/metadata.db` to `/tmp` on cold start and points the model cache (`FASTEMBED_CACHE_PATH`, `HF_HOME`) there too.
- [.vercelignore](../.vercelignore) keeps `docs/` and `tests/` out of the backend upload. Do not add `frontend/` to it: Vercel applies it to the frontend project's git builds too and would break them.
- Embeddings use `fastembed` (ONNX), which gives the same vectors as sentence-transformers (cosine 1.0 against the stored ones).

## Environment variables

| Project | Variable | Value |
|---|---|---|
| `hdfc-mf-rag-api` | `GROQ_API_KEY` | your Groq key |
| `hdfc-mf-rag-api` | `ALLOWED_ORIGINS` | `https://hdfc-mf-rag-chat.vercel.app` (comma-separate more) |
| `hdfc-mf-rag-chat` | `VITE_API_BASE` | `https://hdfc-mf-rag-api.vercel.app` (baked in at build; redeploy after changing) |

## Deploying

- Frontend: push to `main` (git-connected, builds from `frontend/`).
- Backend: `npx vercel deploy --prod` from the repo root (linked to `hdfc-mf-rag-api`).

## Free-tier limits

- The first request after idle is a cold start: the function copies data, downloads the ~65 MB embedding model and loads it (~10 s). Warm requests take ~1-2 s.
- Groq free tier is rate limited; the code retries with backoff.
- Vercel Hobby is non-commercial use only.
