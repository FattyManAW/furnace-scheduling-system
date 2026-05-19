# 干式套管最佳化排爐系統 — API 文件

**版本**：v2.0.0 | **Base URL**：`http://localhost:8002` | **格式**：JSON

---

## 總覽

| 資源 | 端點 | 說明 |
|------|------|------|
| Health | `GET /`、`GET /health` | 健康檢查 |
| Orders | `/api/v1/orders` | 訂單 CRUD + 批量匯入 |
| Molds | `/api/v1/molds` | 模具庫存管理 |
| Kilns | `/api/v1/kilns` | 干燥罐查詢 |
| Schedule | `/api/v1/schedule` | 排程優化 + 結果查詢 |
| Reports | `/api/v1/reports` | 儀表板統計 + CSV/JSON 匯出 |
| Docs | `/docs`、`/openapi.json` | Swagger UI + OpenAPI 規格 |

---

## 認證

目前為**內部系統**，無需 API Key 或 JWT。部署到公網時建議加入 CORS 白名單（`ALLOWED_ORIGINS` 環境變數）。

---

## 1. Health

### `GET /`

回傳系統基本資訊。

**Response 200**
```json
{
  "name": "干式套管最佳化排爐系統",
  "version": "2.0.0",
  "docs": "/docs",
  "api": "/openapi.json"
}
```

### `GET /health`

簡單存活檢查。

**Response 200**
```json
{ "status": "ok" }
```

---

## 2. Orders — `/api/v1/orders`

### `GET /` — 訂單列表

| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `skip` | int | 0 | 分頁偏移 |
| `limit` | int | 100 | 每頁筆數（1–500） |
| `status` | string | — | 篩選：pending / scheduled / completed |
| `search` | string | — | 搜尋 plan_no 或 contract_no |

**Response 200**
```json
[
  {
    "id": 1,
    "plan_no": "PO-2026-0001",
    "contract_no": "C-2026-100",
    "voltage_kv": 220.0,
    "current_a": 150.0,
    "qty": 10,
    "delivery_date": "2026-06-30",
    "product_from": "raw",
    "product_to": "finished",
    "status": "pending",
    "notes": null,
    "created_at": "2026-05-19T08:00:00",
    "updated_at": "2026-05-19T08:00:00"
  }
]
```

### `GET /count` — 訂單數量

| 參數 | 類型 | 說明 |
|------|------|------|
| `status` | string | 可選篩選 |

**Response 200**
```json
{ "count": 251 }
```

### `GET /{order_id}` — 單筆訂單

**Response 200**：同上 OrderOut  
**Response 404**：`{"detail":"訂單不存在"}`

### `POST /` — 新增訂單

**Request Body**
```json
{
  "plan_no": "PO-2026-0100",
  "contract_no": "C-2026-200",
  "voltage_kv": 220.0,
  "current_a": 150.0,
  "qty": 10,
  "delivery_date": "2026-07-15",
  "product_from": "raw",
  "product_to": "finished",
  "status": "pending",
  "notes": ""
}
```

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `plan_no` | string | ✅ | 計劃單號（唯一） |
| `voltage_kv` | float | ✅ | 電壓 (kV) |
| `current_a` | float | ✅ | 電流 (A) |
| `qty` | int | ✅ | 數量 |
| `contract_no` | string | — | 合約編號 |
| `delivery_date` | string | — | 交期 (YYYY-MM-DD) |
| `product_from` | string | — | 原料規格 |
| `product_to` | string | — | 成品規格 |
| `status` | string | — | 預設 pending |
| `notes` | string | — | 備註 |

**Response 201**：OrderOut  
**Response 400**：`{"detail":"計劃單號 PO-xxx 已存在"}`

### `PUT /{order_id}` — 修改訂單

**Request Body**（所有欄位可選）
```json
{ "status": "scheduled", "qty": 12 }
```

**Response 200**：OrderOut  
**Response 404**：`{"detail":"訂單不存在"}`

### `DELETE /{order_id}` — 刪除訂單

**Response 200**
```json
{ "deleted": true, "order_id": 1 }
```

### `POST /bulk-import` — 批量匯入

**Request Body**
```json
[
  { "plan_no": "PO-001", "voltage_kv": 220.0, "current_a": 150.0, "qty": 5 },
  { "plan_no": "PO-002", "voltage_kv": 110.0, "current_a": 80.0, "qty": 3 }
]
```

**Response 200**
```json
{ "imported": 2, "skipped": 0 }
```

---

## 3. Molds — `/api/v1/molds`

### `GET /` — 模具列表

| 參數 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `skip` | int | 0 | 分頁偏移 |
| `limit` | int | 100 | 每頁筆數（1–500） |
| `low_stock` | bool | false | 只顯示庫存 ≤ 3 |

**Response 200**
```json
[
  {
    "id": 1,
    "mold_no": "M-001",
    "outer_dia": 150.0,
    "inner_dia": 120.0,
    "length": 300.0,
    "stock_qty": 5,
    "location": "A區-3架",
    "status": "available",
    "notes": null,
    "created_at": "2026-05-19T08:00:00"
  }
]
```

### `GET /count` — 模具數量

**Response 200**
```json
{ "count": 16 }
```

### `GET /{mold_id}` — 單筆模具

**Response 200**：MoldOut  
**Response 404**：`{"detail":"模具不存在"}`

### `POST /` — 新增模具

**Request Body**
```json
{
  "mold_no": "M-020",
  "outer_dia": 150.0,
  "inner_dia": 120.0,
  "length": 300.0,
  "stock_qty": 10,
  "location": "B區-1架",
  "status": "available"
}
```

**Response 201**：MoldOut  
**Response 400**：`{"detail":"模具編號 M-020 已存在"}`

### `PUT /{mold_id}` — 修改模具

**Request Body**（所有欄位可選）

**Response 200**：MoldOut

### `POST /{mold_id}/stock` — 調整庫存

| 參數 | 類型 | 說明 |
|------|------|------|
| `delta` | int | 正數=入庫，負數=出庫 |
| `reason` | string | 調整原因 |

**Response 200**
```json
{
  "mold_id": 1,
  "mold_no": "M-001",
  "new_stock_qty": 8,
  "delta": 3,
  "reason": "restock"
}
```

---

## 4. Kilns — `/api/v1/kilns`

### `GET /` — 干燥罐列表

**Response 200**
```json
[
  {
    "id": 1,
    "kiln_no": "K-01",
    "name": "干燥罐一号",
    "inner_dia": 500.0,
    "height": 1200.0,
    "schemes": { "A": [10, 20], "B": [15] },
    "created_at": "2026-05-19T08:00:00"
  }
]
```

### `GET /{kiln_id}` — 單一干燥罐

**Response 200**：同上 item  
**Response 404**

---

## 5. Schedule — `/api/v1/schedule`

### `POST /optimize` — 執行排程優化

**Request Body**
```json
{
  "order_ids": [1, 2, 3],
  "strategy": "deadline"
}
```

| 欄位 | 類型 | 預設 | 說明 |
|------|------|------|------|
| `order_ids` | int[] | 全部 | 指定排程的訂單 ID |
| `strategy` | string | deadline | deadline / fill / balance |

**Response 200**
```json
{
  "summary": {
    "total_orders": 251,
    "scheduled_orders": 251,
    "skipped_orders": 0,
    "total_hours": 12345.6,
    "kilns_used": 16
  },
  "kiln_summary": [
    { "kiln_id": 1, "kiln_no": "K-01", "orders_count": 16, "total_hours": 800.0 }
  ],
  "schedule": [
    {
      "id": 1,
      "kiln_id": 1,
      "plan_no": "PO-0001",
      "contract_no": "C-100",
      "voltage_kv": 220.0,
      "current_a": 150.0,
      "qty": 10,
      "delivery_date": "2026-06-30",
      "mold_od": 120.0,
      "mold_len": 200.0,
      "est_hours": 48.0,
      "status": "scheduled",
      "created_at": "2026-05-19T08:00:00"
    }
  ],
  "warnings": []
}
```

### `GET /result` — 查詢當前排程結果

**Response 200**：同上 ScheduleResult

### `GET /{kiln_id}/schedule` — 指定干燥罐的排程

**Response 200**：ScheduleEntryOut 列表

---

## 6. Reports — `/api/v1/reports`

### `GET /dashboard` — 儀表板統計

**Response 200**
```json
{
  "total_orders": 251,
  "pending_orders": 0,
  "scheduled_orders": 251,
  "completed_orders": 0,
  "overdue_orders": 5,
  "total_kilns": 28,
  "active_kilns": 16,
  "total_molds": 16,
  "total_hours_scheduled": 12345.6,
  "daily_hour_cap": 800.0
}
```

### `GET /orders/csv` — 匯出訂單 CSV

| 參數 | 類型 | 說明 |
|------|------|------|
| `status` | string | 可選篩選 |

**Response 200**：`text/csv` 下載

### `GET /schedule/csv` — 匯出排程 CSV

**Response 200**：`text/csv` 下載

### `GET /orders/json` — 匯出訂單 JSON

| 參數 | 類型 | 說明 |
|------|------|------|
| `status` | string | 可選篩選 |

**Response 200**：Order 物件列表

---

## 錯誤碼總表

| 狀態碼 | 說明 |
|--------|------|
| 200 | 成功 |
| 201 | 建立成功 |
| 400 | 請求參數錯誤／重複 |
| 404 | 資源不存在 |
| 422 | 請求格式驗證失敗 |
| 500 | 伺服器內部錯誤 |

---

## Swagger UI

部署後訪問 `http://<host>:8002/docs` 即可使用互動式 API 文件，支援 Try it out 直接測試。

OpenAPI 規格：`http://<host>:8002/openapi.json`

---

*文件結束 — 2026-05-19*