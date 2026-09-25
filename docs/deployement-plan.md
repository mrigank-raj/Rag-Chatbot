# Deployment Plan (free tier only)

## Target architecture

| Piece | Platform | Why |
|---|---|---|
| Backend (FastAPI + ChromaDB + embeddings) | **Hugging Face Spaces** (Docker SDK, CPU basic) | Free, 16 GB RAM / 2 vCPU. The backend loads `sentence-transformers` (PyTorch) + `bge-small`, which needs ~700 MB+ and will OOM on Render/Railway free tiers (512 MB). |
| Frontend (Vite + React) | **Vercel** (Hobby) — Netlify or Cloudflare Pages work identically | Free static hosting, auto-deploys from GitHub. |
| LLM | **Groq** free tier | Already used; only needs `GROQ_API_KEY`. |
| Daily data refresh | **GitHub Actions** (already running) | Already commits fresh `vectorstore/` + `db/metadata.db` to `main`. |

Total cost: $0. No credit card needed on any of these.

```
User ──> Vercel (React) ──HTTPS──> HF Space (FastAPI) ──> Groq API
                                        │
                        vectorstore/ + db/ baked into image
                                        ▲
        GitHub Action (daily) ── commits ── GitHub main ── sync ── HF Space repo
```

## Free-tier limits to accept

- **HF Space sleeps after 48 h without traffic**; the first request afterwards takes ~1–2 min to wake. Fine for a demo. Free workaround: ping `/api/health` every few hours with a cron (GitHub Action or cron-job.org).
- **Ephemeral disk**: nothing written at runtime survives a restart. This is fine because the vectorstore is read-only at runtime and refreshed via git.
- **Groq free tier** is rate limited; the existing `tenacity` retries help. Expect throttling under heavy use.
- Vercel Hobby is non-commercial use only.

## Code changes required (one-time)

1. **Frontend API URL** — [frontend/src/App.jsx:5](frontend/src/App.jsx#L5) hardcodes `http://127.0.0.1:8000/api/chat`. Change to:
   ```js
   const API_URL = `${import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'}/api/chat`;
   ```
2. **Dockerfile** — HF Spaces expects port **7860** and runs as a non-root user (uid 1000). Replace the tail of the [Dockerfile](Dockerfile) with:
   ```dockerfile
   RUN useradd -m -u 1000 user && chown -R user /app
   USER user
   ENV HF_HOME=/app/.cache
   # Pre-download the embedding model at build time so cold starts are fast
   RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
   EXPOSE 7860
   CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
   ```
   (Add `--extra-index-url https://download.pytorch.org/whl/cpu` with `torch` to `requirements.txt` if the build is slow or large; CPU-only torch is enough.)
3. **CORS** — in [src/api/main.py:22](src/api/main.py#L22) replace `allow_origins=["*"]` with your Vercel URL once known.
4. **`.dockerignore`** — add one excluding `frontend/`, `.git`, `.env`, `__pycache__`, `.pytest_cache`, `tests/` to keep the image small and keep `.env` out of it.

## Step 1 — Deploy backend on Hugging Face Spaces

1. Create a free account at huggingface.co → **New Space** → SDK **Docker** → Blank template → visibility Public (private also works) → name e.g. `hdfc-mf-rag-api`.
2. In the Space **Settings → Variables and secrets** add:
   - Secret: `GROQ_API_KEY`
   - Variables (optional, defaults exist in [src/utils/config.py](src/utils/config.py)): `GROQ_MODEL`, `EMBEDDING_MODEL`
3. Add this YAML frontmatter at the very top of a `README.md` in the Space repo:
   ```yaml
   ---
   title: HDFC MF RAG API
   sdk: docker
   app_port: 7860
   ---
   ```
4. Push code to the Space (it is a git repo). Easiest: add it as a second remote and push `main`:
   ```bash
   git remote add hf https://huggingface.co/spaces/<your-username>/hdfc-mf-rag-api
   git push hf main
   ```
   Use an HF access token (Settings → Access Tokens, **write**) as the password. The project's README frontmatter must be present on the Space's copy — keep a small `README.md` variant only for the Space, or add the frontmatter to the repo README.
5. Wait for the build (5–10 min first time). Verify:
   `https://<your-username>-hdfc-mf-rag-api.hf.space/api/health` returns OK.

## Step 2 — Deploy frontend on Vercel

1. vercel.com → **Add New Project** → import `mrigank-raj/Rag-Chatbot`.
2. **Root Directory**: `frontend`. Framework preset: Vite (auto-detected). Build `npm run build`, output `dist`.
3. **Environment variable**: `VITE_API_BASE = https://<your-username>-hdfc-mf-rag-api.hf.space`
4. Deploy. Copy the resulting `*.vercel.app` URL.
5. Put that URL into the backend CORS allowlist (code change 3), push to the Space again.

## Step 3 — Keep data fresh automatically

The existing workflow [ingest_cron.yml](.github/workflows/ingest_cron.yml) already commits the updated vectorstore to GitHub `main` daily. Add a final step so the Space rebuilds with it:

1. Add repo secret `HF_TOKEN` (HF write token) in GitHub → Settings → Secrets → Actions.
2. Append to the workflow's steps (after the commit/push step):
   ```yaml
   - name: Sync to Hugging Face Space
     env:
       HF_TOKEN: ${{ secrets.HF_TOKEN }}
     run: |
       git push --force https://<your-username>:$HF_TOKEN@huggingface.co/spaces/<your-username>/hdfc-mf-rag-api HEAD:main
   ```
   Vercel needs nothing: it redeploys on pushes to `main`, and frontend code is unchanged by ingestion.

## Verification checklist

- [ ] `GET <space-url>/api/health` returns 200
- [ ] Ask a fund question in the Vercel UI → grounded answer with sources
- [ ] Browser console shows no CORS errors
- [ ] Trigger the ingest workflow manually (Actions → *Run workflow*) → Space rebuilds and still answers
- [ ] Leave idle >48 h, confirm the Space wakes on next request

## Alternatives considered

- **Render free web service**: simpler, but 512 MB RAM is too small for PyTorch + embeddings, and it sleeps after 15 min idle.
- **Railway / Fly.io**: no longer truly free (trial credits / card required).
- **Google Cloud Run**: has a free tier but needs a billing account and more setup; not chosen for "free only, zero card".

## Later, if needed

- Stop the cold starts: uptime ping, or move to a paid always-on tier.
- Protect the API from abuse: add rate limiting or a shared header token between frontend and backend (the endpoint is public and each call spends Groq quota).
