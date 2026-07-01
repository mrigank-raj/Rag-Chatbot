# Phase-wise Evaluation Framework (`eval.md`)

This document defines the evaluation criteria, metrics, and verification steps for each phase of the HDFC Mutual Fund FAQ Assistant project. Completing the evaluation for a phase ensures that the system is ready to progress to the next stage.

---

## Phase 1: Project Setup & Foundation

**Objective:** Ensure the repository, environment, and databases are properly initialized.

### Evaluation Steps
1. **Dependency Check:** Run `pip check` to ensure all packages in `requirements.txt` (FastAPI, Langchain-Groq, sentence-transformers, ChromaDB, etc.) are installed without conflicts.
2. **Environment Validation:** Verify `.env` loads correctly using `src/utils/config.py` and that `GROQ_API_KEY` is present.
3. **Database Initialization:** Run the SQLite initialization script and verify `metadata.db` is created in the `db/` folder.
4. **URL Configuration:** Verify `data/urls.json` contains exactly 5 Groww URLs and parses as valid JSON.

### Success Criteria
- [x] Application can import all required libraries without `ModuleNotFoundError`.
- [x] SQLite database contains `sources` and `query_logs` tables with 0 rows.
- [x] The `docs/` and `src/` directory structures match the architecture.

---

## Phase 2: Data Ingestion Pipeline

**Objective:** Ensure web scraping, chunking, and vector embedding are functioning correctly.

### Evaluation Steps
1. **Scraping Verification:** Check `data/raw/` to ensure 5 `.txt` files were created and that HTML tags (navbars, ads) were successfully stripped out.
2. **Chunking Quality:** Inspect the chunk outputs from `RecursiveCharacterTextSplitter`. Ensure chunks are roughly 500 characters and sentences are not abruptly cut off.
3. **Vector Store Validation:** Query ChromaDB using `chroma_client.get()` to verify that the `hdfc_mf_chunks` collection is populated and that embeddings have the correct dimensionality for `BAAI/bge-small-en-v1.5` (384 dimensions).
4. **Metadata DB State:** Check the SQLite `sources` table to ensure 5 rows exist with `status = 'active'` and `chunk_count > 0`.

### Success Criteria
- [x] 100% of the 5 Groww URLs successfully scraped.
- [x] ChromaDB persists vectors to the `./vectorstore` directory.
- [x] Every chunk contains valid metadata (`source_url`, `scheme_name`).

---

## Phase 3: RAG Core Pipeline

**Objective:** Validate the accuracy of Query Classification, Semantic Retrieval, and LLM Generation.

### Evaluation Steps
1. **Classifier Evaluation:** Run a test script with 15 queries (5 Factual, 5 Advisory, 5 Out-of-Scope) and measure precision/recall.
2. **Retriever Hit Rate (Top-K):** Run a test script with 10 factual queries. Check if the chunk containing the true answer is present in the Top-3 results.
3. **Generator Groundedness:** Ask the LLM 5 factual questions based on the retrieved context. Verify that the LLM does not hallucinate information outside the context.
4. **Generator Format Check:** Assert that the LLM response is ≤ 3 sentences and contains exactly 1 valid citation from the metadata.

### Success Criteria
- [x] **Classifier Accuracy:** > 95% (Crucial for safety).
- [x] **Retrieval Recall@3:** > 85% (Relevant context is successfully found).
- [x] **Hallucination Rate:** 0% (LLM strictly answers "I don't know" if context is missing).
- [x] **Formatting:** 100% compliance with length, footer, and citation rules.

---

## Phase 4: API Layer

**Objective:** Ensure endpoints are accessible, secure, and handle errors gracefully.

### Evaluation Steps
1. **Endpoint Health:** Hit `/api/health` and verify a `200 OK` response.
2. **E2E Chat Request:** Send a POST request to `/api/chat` with a factual query and verify the structured JSON response matches the `ChatResponse` Pydantic schema.
3. **PII Injection Test:** Send a POST request containing a 10-digit phone number or PAN format. Ensure the API returns a `400 Bad Request` or blocks the query.
4. **Rate Limit Test:** Send 35 rapid concurrent requests to `/api/chat`. Ensure the 31st request returns a `429 Too Many Requests`.

### Success Criteria
- [x] API successfully processes valid requests in `< 3 seconds`.
- [x] PII Regex blocks 100% of blatant PII attempts.
- [x] Invalid JSON payloads return standard `422 Unprocessable Entity` errors.

---

## Phase 5: Frontend Chat UI

**Objective:** Verify user experience, interface rendering, and backend integration.

### Evaluation Steps
1. **Static Rendering:** Open `frontend/index.html` in a browser. Check that the disclaimer banner is clearly visible and styling applies correctly.
2. **Interactive Elements:** Click the 3 "Example Question" chips and ensure they auto-populate the input and trigger a chat request.
3. **Response Rendering:** Verify that the JSON response from the API is parsed correctly:
   - Chat bubbles align correctly (User right, Bot left).
   - Citation links are clickable and open in a new tab.
   - The "Last updated" footer is visible.
4. **Refusal Rendering:** Trigger an advisory question and ensure the polite refusal and educational link (AMFI/SEBI) render cleanly.

### Success Criteria
- [x] UI handles loading states (typing indicator).
- [x] UI gracefully displays error banners if the backend is down (e.g., 503 errors).
- [x] No console errors in the browser Developer Tools.

---

## Phase 6: Testing & Dockerization

**Objective:** Finalize automated tests and ensure containerized portability.

### Evaluation Steps
1. **Pytest Suite:** Run `pytest tests/` and ensure 100% of written tests pass.
2. **Docker Build:** Run `docker build -t hdfc-rag .` and verify the image builds without layer failures.
3. **Container Execution:** Run the Docker container, exposing port `8000`. Navigate to `http://localhost:8000` and perform a manual end-to-end test.
4. **Log Verification:** Check the SQLite `query_logs` table to ensure that interactions during the Docker test were correctly persisted to the mapped volume.

### Success Criteria
- [x] All unit tests pass locally and in CI (if applicable).
- [x] The Docker image correctly bundles the scraped vectors (or successfully creates them at runtime).
- [x] The application functions identically in Docker as it does on the local machine.
