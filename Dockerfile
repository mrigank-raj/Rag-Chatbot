FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Optional: Run ingestion at build time to bake the vectorstore and metadata.db directly into the image
# If you prefer to ingest data at runtime or mount a volume, comment this out.
# RUN python scripts/ingest.py

# Hugging Face Spaces runs containers as uid 1000 and expects port 7860
RUN useradd -m -u 1000 user && chown -R user /app
USER user
ENV HF_HOME=/app/.cache
# Pre-download the embedding model so cold starts don't fetch it
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

EXPOSE 7860

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
