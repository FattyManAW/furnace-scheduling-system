# 排爐系統 (Furnace Scheduling System) — PLAYBOOK

> Elite Squad 品質改造部隊 · 操作手冊 · 2026-05-21

## 🚨 緊急聯絡

| 角色 | 負責 |
|------|------|
| CRIS SWAT | 系統開發/維護 |
| Elite Squad | 品質監督 |

## 📡 服務架構

| 服務 | URL | 埠號 |
|------|-----|------|
| 前端 Dashboard | `http://<host>:8030` | 8030 |
| API Backend | `http://<host>:8002` | 8002 |
| API Health | `http://<host>:8002/health` | — |

## 🔄 日常操作

### 啟動
```bash
docker compose up -d
```

### 停止
```bash
docker compose down
```

### 重啟
```bash
docker compose restart
```

### 查看日誌
```bash
docker compose logs -f --tail=50 furnace-api
docker compose logs -f --tail=50 furnace-nginx
```

### 健康檢查
```bash
curl -s http://localhost:8002/health
curl -s http://localhost:8030/
```

## 🔧 常見問題

### API 回傳 500
1. 檢查 DB 連線：`docker exec furnace-api python3 -c "from database import engine; engine.connect()"`
2. 重啟 API：`docker compose restart furnace-api`

### 前端顯示空白
1. 確認 API 正常：`curl http://localhost:8002/health`
2. 重啟 nginx：`docker compose restart furnace-nginx`

### Docker container unhealthy
1. `docker inspect furnace-api --format '{{.State.Health.Status}}'`
2. 確認 HEALTHCHECK 用 `127.0.0.1`（不是 `localhost`）
3. 如持續 unhealthy → `docker compose down && docker compose up -d`

## 🧪 測試

```bash
# Backend tests
pip install pytest pytest-cov
pytest backend/tests/ -v

# E2E test
python3 tests/test_e2e.py
```

## 📊 CI/CD

| Gate | 狀態 |
|------|------|
| Lint (ruff) | ✅ quality-gate.yml |
| Test (pytest) | ✅ CI pipeline |
| Docker Build | ✅ deploy.yml |
| Deploy | ⚠️ 條件式（需 SSH secrets） |

## 🔒 安全

- Dockerfile HEALTHCHECK 必須用 `127.0.0.1`（非 `localhost`）
- 禁止 hardcoded secrets
- `FastAPI(redirect_slashes=False)` 標配

---

*Elite Squad · Day 2 · 自動生成*