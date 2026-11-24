FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    KMP_DUPLICATE_LIB_OK=TRUE \
    OMP_NUM_THREADS=1 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    TQDM_DISABLE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download default embedding & cross-encoder models into container cache
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('all-MiniLM-L6-v2'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

COPY backend ./backend

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
