# Deployment Plan (free tier only)

| Piece | Platform | Notes |
|---|---|---|
| Backend (FastAPI + ChromaDB + fastembed) | **Render** free web service | Config in [render.yaml](../render.yaml). ~280 MB RAM, fits the 512 MB limit. |
| Frontend (Vite + React) | **Vercel** Hobby | Root directory `frontend`. |
| LLM | **Groq** free tier | Model set by `GROQ_MODEL` (default `openai/gpt-oss-20b`). |
| Daily data refresh | **GitHub Actions** | Commits fresh `vectorstore/` to `main`; Render auto-redeploys on that push. |

```
User -> Vercel (React) -> Render (FastAPI) -> Groq
                              ^ vectorstore/ + db/ come from the repo
GitHub Action (daily) -> commit to main -> Render redeploys
```

## Why fastembed, not sentence-transformers

PyTorch pushes the backend past Render's 512 MB. `fastembed` runs the same
`BAAI/bge-small-en-v1.5` model on ONNX and produces identical vectors (cosine 1.0
against the stored ones), so the existing vectorstore is unchanged.

## Free-tier limits

- Render free services sleep after 15 min idle; the first request afterwards takes ~30-60 s. The UI shows "Checking the scheme pages" meanwhile.
- Free instances get ~750 hours/month, enough for one always-available service.
- Groq free tier is rate limited; the code retries with backoff.
- Vercel Hobby is non-commercial use only.

## Steps

### 1. Backend on Render
1. Sign in at https://dashboard.render.com with GitHub.
2. Open https://dashboard.render.com/blueprint/new?repo=https://github.com/mrigank-raj/Rag-Chatbot and apply the blueprint (`render.yaml`).
3. When prompted, set `GROQ_API_KEY`. Leave `ALLOWED_ORIGINS` for step 3.
4. Wait for the first build (~5 min). Check `https://<service>.onrender.com/` returns the welcome message and `/api/health` reports healthy.

### 2. Frontend on Vercel
1. Project `hdfc-mf-rag-chat` is already linked to this repo.
2. Set env var `VITE_API_BASE=https://<service>.onrender.com` (Production), then redeploy.

### 3. Lock down CORS
In Render, set `ALLOWED_ORIGINS=https://<your-vercel-domain>` (comma-separate multiple origins) and redeploy.

## Verification

- [ ] `GET <render-url>/api/health` returns healthy
- [ ] A fund question in the Vercel UI returns a sourced answer
- [ ] No CORS errors in the browser console
- [ ] Manually run the ingest workflow; Render redeploys and still answers
