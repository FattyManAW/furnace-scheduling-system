# ── 干式套管最佳化排爐系統 Dockerfile ──────────────────────────
# Multi-stage: build → slim runtime

FROM python:3.9-slim AS builder

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY backend/ ./backend/
COPY data/    ./backend/data/

# ── 建置時注入 commit hash（供 /health endpoint 回傳）───────
ARG GIT_COMMIT=unknown
RUN echo "${GIT_COMMIT}" > /app/GIT_COMMIT

WORKDIR /app/backend

# ── Startup wrapper: 自動建表 + seed（僅在 DB 不存在時）───────
RUN printf '#!/bin/bash\nset -e\nDB_FILE="$(python3 -c "import database; print(database.SQLALCHEMY_DATABASE_URL.replace(\"sqlite:///\",\"\"))" 2>/dev/null || echo /app/backend/data/furnace_schedule.db)"\nif [ ! -f "$DB_FILE" ]; then\n  echo "📦 First run — seeding database..."\n  python3 -c "from database import engine, Base; Base.metadata.create_all(bind=engine); from seed_data import seed_all; seed_all(); print(\"\xE2\x9C\x85 DB seeded\")"\nelse\n  echo "✅ DB exists, skipping seed"\nfi\nexec python3 -m uvicorn main:app --host 0.0.0.0 --port 8002\n' > /start.sh && chmod +x /start.sh

RUN printf '#!/usr/bin/env python3\nimport urllib.request,sys\nfor p in ["/health","/api/v1/orders/count"]:\n try:urllib.request.urlopen(f"http://127.0.0.1:8002{p}",timeout=5)\n except Exception as e:sys.exit(1)\n' > /healthcheck.py && chmod +x /healthcheck.py

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s CMD python3 /healthcheck.py
EXPOSE 8002
CMD ["/start.sh"]
