# -----------------------------
# Stage 1 — Builder
# -----------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps (needed for psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

RUN pip install --user --no-cache-dir -r requirements.txt

# -----------------------------
# Stage 2 — Runtime
# -----------------------------
FROM python:3.12-slim

WORKDIR /app

# COPY INstalled packages
COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

# Copy project files
COPY app ./app

# Export FAST API port
EXPOSE 8000

CMD ["python", "-m", "app.main"]