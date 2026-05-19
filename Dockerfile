# ── 干式套管最佳化排爐系統 Dockerfile ──────────────────────────
# Multi-stage: build → slim runtime (~180 MB)
# Build:  docker build -t furnace-api .
# Run:    docker run -d -p 8002:8002 --name furnace furnace-api
#
# Python 3.9 slim — 最小化映像 + 安全掃描就緒

FROM python:3.9-slim AS builder

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user --no-deps -r requirements.txt \
    && pip install --no-cache-dir --user \
       fastapi uvicorn sqlalchemy pydantic python-multipart

# ── Runtime stage ─────────────────────────────────────────────────
FROM python:3.9-slim

# 安全加固：非 root 用戶
RUN useradd --create-home --shell /bin/bash furnace
WORKDIR /app

# 複製 pip packages
COPY --from=builder /root/.local /home/furnace/.local
ENV PATH=/home/furnace/.local/bin:$PATH

# 複製 source（只複製 backend，不含 data/）
COPY backend/ ./backend/

WORKDIR /app/backend

# 預建資料庫
RUN python3 -c 'from database import engine, Base; Base.metadata.create_all(bind=engine); from seed_data import seed_all; seed_all(); print("✅ Database seeded")'

# ── 健康檢查腳本（多端點驗證）─────────────────────────────────
RUN printf '#!/usr/bin/env python3\n\
import urllib.request, json, sys\n\
endpoints = [\n\
    ("/health", "health"),\n\
    ("/api/v1/orders/count", "orders"),\n\
]\n\
ok = True\n\
for path, name in endpoints:\n\
    try:\n\
        req = urllib.request.Request(f"http://localhost:8002{path}")\n\
        with urllib.request.urlopen(req, timeout=5) as resp:\n\
            if resp.status != 200:\n\
                print(f"FAIL {name}: HTTP {resp.status}", file=sys.stderr)\n\
                ok = False\n\
    except Exception as e:\n\
        print(f"FAIL {name}: {e}", file=sys.stderr)\n\
        ok = False\n\
sys.exit(0 if ok else 1)\n\
' > /healthcheck.py && chmod +x /healthcheck.py

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
  CMD python3 /healthcheck.py

# 切換非 root
USER furnace

EXPOSE 8002

STOPSIGNAL SIGTERM

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]