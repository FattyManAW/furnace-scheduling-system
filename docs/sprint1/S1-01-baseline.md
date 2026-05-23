# S1-01 現狀基準報告

**生成時間**: 2026-05-24 00:32 Asia/Shanghai
**來源 commit**: `1dad49e`
**執行者**: Forge (Squad Alpha Backend)
**目標**: 排爐系統後端核心重建 — 現狀基準

---

## 1. OpenAPI 3.0 Baseline

- **來源**: 運行中 :8005 API (`GET /openapi.json`)
- **端點總數**: 42 (29 paths)
- **產出檔案**: `docs/sprint1/openapi-baseline.json`
- **已覆蓋模組**: orders, molds, kilns, schedule, reports, process-steps, health

所有端點已含 input/output schema（Pydantic v2 自動生成）。缺失項目：
- 無 `summary`/`description` 多語言支援（僅英文）
- 無 `operationId` 命名規範
- `schedule` endpoints 無範例 response payload

---

## 2. 測試覆蓋率

```text
TOTAL  1899 statements, 492 missed, 74% coverage
44 tests, 43 passed + 1 reroute (pending)
```

### 前 5 覆蓋最低模組

| 模組 | 語句 | 覆蓋 | 風險 |
|------|------|:---:|------|
| `engine/validator.py` | 43 | 9% | 🔴 排程品質驗證完全無測 |
| `api/schedule.py` | 135 | 29% | 🔴 優化排程 API 核心未測 |
| `api/reports.py` | 58 | 34% | 🟠 報表匯出未測 |
| `crud.py` | 208 | 44% | 🟠 CRUD 層大量未測 |
| `api/kilns.py` | 44 | 48% | 🟡 干燥罐 API 部分未測 |

### 覆蓋 ≥90% 模組（5 個）

`api/orders.py` 91%, `engine/reroute.py` 94%, `schemas.py` 94%, `models.py` 100%, `engine/data_layer.py` 100%

### → 達標路徑

Target: ≥80% → 需補充 **最少 114 statements**：

| 優先級 | 模組 | 新增測試 | 預估新增 |
|:--:|------|------|:--:|
| P0 | `api/schedule.py` | API route tests | +40 |
| P0 | `crud.py` | CRUD integration | +30 |
| P1 | `engine/validator.py` | Unit tests | +25 |
| P1 | `api/reports.py` | CSV/JSON export | +15 |
| P2 | `api/kilns.py` | CRUD route tests | +10 |

---

## 3. CI Pipeline 審計

### 現有 Workflow

| 檔案 | Gate | 狀態 |
|------|------|:--:|
| `deploy.yml` | Lint → Test → Docker Build | ✅ 有效 |
| `otd-ci.yml` | 6-gate pipeline (OTD-specific) | ✅ 含 threshold |
| `quality-gate.yml` | Ruff + Import check + DB seed | ⚠️ threshold=60% |

### 缺口

1. **quality-gate.yml 的 coverage threshold 仍為 60%**（應升至 80%）
2. **無 contract test**（OpenAPI ↔ frontend 對接）
3. **缺 Docker smoke test**（deploy.yml 有 build 但無 docker compose up 驗證）

---

## 4. 建議優先級

| # | 項目 | 預估 | 優先 |
|--:|------|-----|:--:|
| 1 | 補測試 → 拉到 80% 覆蓋 | 2h | P0 |
| 2 | quality-gate coverage 升 80% | 5min | P0 |
| 3 | OpenAPI spec enhancement (description/tags) | 30min | P1 |
| 4 | Contract test scaffolding | 1h | P1 |
| 5 | Docker smoke test in CI | 30min | P2 |

---

## 5. 結論

後端核心已 74% 測試覆蓋，CI pipeline 有 3-job 結構，42 API endpoints 全有 OpenAPI spec。最大風險點是 `validator.py` (9%) 和 `api/schedule.py` (29%) 的測試空白。S1-01 目標 "≥80% 覆蓋" 需至少 114 statements 新測試，預計 2 小時。