# ── 干式套管最佳化排爐系統 Dockerfile ──────────────────────────────
# Multi-stage: build → slim runtime
# Usage: docker build -t furnace-api . && docker run -p 8002:8002 furnace-api

FROM python:3.9-slim AS builder

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────
FROM python:3.9-slim

WORKDIR /app

# Copy pip packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy backend source + data
COPY backend/ ./backend/
COPY data/    ./backend/data/

WORKDIR /app/backend

# Pre-seed database at build time
RUN python3 -c 'from database import engine, Base; Base.metadata.create_all(bind=engine); from seed_data import seed_all; seed_all(); print("✅ Database seeded")'

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"

EXPOSE 8002

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]