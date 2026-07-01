# HDFC Mutual Fund Facts-Only RAG Assistant 🚀🌌

An end-to-end Retrieval-Augmented Generation (RAG) chatbot designed exclusively to provide objective, factual information about 5 specific HDFC Mutual Fund schemes. 

Built with **FastAPI**, **LangChain**, **ChromaDB**, and **Groq (Llama 3)**, this application strictly prevents hallucination and automatically refuses advisory or out-of-scope queries. It features a premium, animated "Galaxy" UI built in React.

## 🌟 Features
- **Facts-Only Guardrails**: Automatically classifies and blocks investment advice ("Should I invest?") and out-of-scope queries (e.g., SBI mutual funds) before hitting the LLM.
- **Automated Data Ingestion**: A GitHub Actions cron job (`05:00 UTC` / `10:30 AM IST`) automatically scrapes the latest fund pages from Groww, updates the local ChromaDB vector store, and pushes changes back to the repository.
- **Source Citations**: Every generated answer strictly includes exactly one verifiable citation link to the official source and a "Last Updated" timestamp.
- **Premium UI**: Immersive, galaxy-themed React frontend with floating chat bubbles, dynamic nebulas, and twinkling stars.
- **Dockerized**: Instantly deployable backend via standard Docker containers.

## 🛠️ Supported Schemes
This assistant relies on official Groww documents for:
1. HDFC Large Cap Fund
2. HDFC Mid-Cap Opportunities Fund
3. HDFC Small Cap Fund
4. HDFC Gold ETF Fund of Fund
5. HDFC Silver ETF Fund of Fund

---

## 🚀 Quickstart (Local Development)

### 1. Prerequisites
- Python 3.11+
- Node.js & npm (for frontend)
- A Groq API Key

### 2. Setup Environment
Clone the repo and install Python dependencies:
```bash
git clone https://github.com/mrigank-raj/Rag-Chatbot.git
cd Rag-Chatbot

# Install python dependencies
pip install -r requirements.txt
```

Create a `.env` file in the root directory (use `.env.example` as a template):
```env
GROQ_API_KEY="your_groq_api_key_here"
GROQ_MODEL="llama-3.3-70b-versatile"
```

### 3. Run the Backend API
```bash
# Start the FastAPI server (runs on port 8000)
python -m uvicorn src.api.main:app --reload --port 8000
```

### 4. Run the React Frontend
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
The immersive chat UI will be available at `http://localhost:5173`.

---

## 🐳 Docker Deployment

To spin up the backend API along with persistent vector volumes:
```bash
docker-compose up --build -d
```
The API will be exposed on `http://localhost:8000`.

---

## 🔄 Automated Daily Data Refresh

The project is configured with a **GitHub Actions CI/CD Pipeline**. 
Every day at `10:30 AM IST`, the `.github/workflows/ingest_cron.yml` workflow fires up an Ubuntu runner that:
1. Scrapes the 5 target URLs.
2. Runs our custom chunking and embedding logic.
3. Updates the `vectorstore/` and `db/metadata.db` files.
4. Commits those database changes seamlessly back to the `main` branch.

You can also trigger this process manually by navigating to the "Actions" tab in this repository and clicking **Run workflow**.

---

## 🧠 Architecture Overview
- **Pipeline Structure**: Classifier ➔ Retriever ➔ Response Generator.
- **Embeddings**: `BAAI/bge-small-en-v1.5` via sentence-transformers.
- **Vector DB**: ChromaDB with scheme-specific metadata filtering.
- **LLM**: Groq (`llama-3.3-70b-versatile`) for ultra-low latency synthesis.

*For deeper technical details, review the `docs/Architecture.md` file!*
