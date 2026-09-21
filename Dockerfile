FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/
COPY data/docs/ ./data/docs/
COPY sql/ ./sql/

# Bake the FAISS index (and the embedding-model download) into the image
# so the container never depends on a local data/faiss_index/ at runtime.
RUN python scripts/build_index.py

EXPOSE 8080

# Cloud Run injects $PORT (defaults to 8080) — never hardcode 8000 here.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
