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

EXPOSE 8000

# Start the FastAPI server using Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
