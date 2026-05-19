# 🔥 干式套管最佳化排爐系統 v2

前後端分離架構 — 基於 FastAPI + React 的工廠排爐最佳化操作系統。

## 系統架構

```
├── backend/                  # FastAPI 後端
│   ├── main.py              # 主程式 + 路由掛載
│   ├── database.py          # SQLAlchemy + SQLite
│   ├── models.py            # ORM 資料模型
│   ├── schemas.py           # Pydantic 驗證Schema
│   ├── crud.py              # 資料庫 CRUD 操作
│   ├── seed_data.py         # JSON → DB 初始匯入
│   ├── api/                 # RESTful API 端點
│   │   ├── orders.py        # 訂單 CRUD
│   │   ├── molds.py         # 模具庫存
│   │   ├── kilns.py         # 干燥罐
│   │   ├── schedule.py      # 排程優化執行
│   │   └── reports.py       # 報表與統計
│   ├── engine/              # 排程邏輯核心
│   │   ├── optimizer.py     # 排程優化引擎
│   │   └── validator.py     # 約束驗證
│   └── data/                # JSON 假資料
│
└── frontend/                # React + Vite 前端
    ├── src/
    │   ├── pages/           # 頁面元件
    │   │   ├── Dashboard.jsx   # 儀表板
    │   │   ├── Orders.jsx      # 訂單管理
    │   │   ├── Molds.jsx       # 模具庫存
    │   │   ├── Schedule.jsx    # 排程設定
    │   │   ├── Gantt.jsx       # 甘特圖
    │   │   ├── Reports.jsx     # 報表匯出
    │   │   └── Settings.jsx    # 系統設定
    │   ├── components/      # 共用元件
    │   ├── lib/api.js       # API client
    │   └── main.jsx         # 入口
    └── dist/                # build 產出（GitHub Pages）
```

## 快速啟動

### 後端

```bash
cd backend

# 1. 安裝 Python 套件
pip install fastapi uvicorn sqlalchemy pydantic

# 2. 初始化資料庫 + 匯入假資料
python seed_data.py --init

# 3. 啟動 API 伺服器
python main.py
# → http://localhost:8002
# → Swagger UI: http://localhost:8002/docs
# → OpenAPI: http://localhost:8002/openapi.json
```

### 前端

```bash
cd frontend

# 1. 安裝 Node 套件
npm install

# 2. 開發模式（proxy 到後端）
npm run dev
# → http://localhost:5173

# 3. Production build
npm run build
# → dist/ 目錄
```

## API 文件

啟動後端後，Swagger UI 會自動在 `/docs` 提供互動式 API 文件。

## 核心 API

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/orders/` | 列出所有訂單 |
| POST | `/api/v1/orders/` | 新增訂單 |
| PUT | `/api/v1/orders/{id}` | 修改訂單 |
| DELETE | `/api/v1/orders/{id}` | 刪除訂單 |
| GET | `/api/v1/molds/` | 模具庫存列表 |
| PUT | `/api/v1/molds/{id}/stock` | 調整庫存 |
| GET | `/api/v1/kilns/` | 干燥罐列表 |
| POST | `/api/v1/schedule/optimize` | 執行排程優化 |
| GET | `/api/v1/schedule/result` | 取得排程結果 |
| GET | `/api/v1/reports/dashboard` | 儀表板統計 |
| GET | `/api/v1/reports/orders/csv` | 匯出訂單 CSV |
| GET | `/api/v1/reports/schedule/csv` | 匯出排程 CSV |

## 排程邏輯

1. **交期優先** — 按交期日期排序訂單
2. **產品→模具映射** — 電壓 × 電流決定產品型號，對應唯一模具規格
3. **模具→爐映射** — 每個爐有多種放置方案（A/B/C/D），根據模具尺寸分配
4. **大產品限制** — 外徑 ≥ 470mm 只能進大槽爐
5. **每日工時上限** — 全局 1098 小時（超標時發出警示）
6. **優先填滿** — 優先分配空閒槽位最多的爐

## 🚀 部署（3 分鐘從零到上線）

### 一鍵啟動（推薦）

```bash
git clone https://github.com/FattyManAW/furnace-scheduling-system.git
cd furnace-scheduling-system
chmod +x start.sh
./start.sh
```

啟動後自動完成：
1. ✅ 檢查 Docker 環境
2. ✅ Clone / 拉取最新程式碼
3. ✅ Build Docker 映像
4. ✅ 初始化資料庫（匯入 251 筆測試訂單）
5. ✅ 啟動 API + Nginx 前端
6. ✅ 健康檢查（驗證所有 API 端點）
7. ✅ 顯示服務 URL + 常用指令

### Docker Compose 手動部署

```bash
# 啟動（後端 + 前端）
docker compose up -d

# 查看日誌
docker compose logs -f

# 重啟
docker compose restart

# 停止（保留資料）
docker compose down

# 完全清除（含資料）
docker compose down -v
```

### 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `PORT` | `8002` | 後端 API port |
| `NGINX_PORT` | `8030` | 前端 nginx port |
| `TZ` | `Asia/Taipei` | 時區 |
| `ALLOWED_ORIGINS` | `localhost:5173,3000` | CORS 允許來源 |

### CI/CD 自動部署

Push 到 `main` 分支即觸發 GitHub Actions：

```
push → test-backend → build-docker → deploy SSH
            ↓
     build-frontend → artifact upload
```

部署目標設定在 `.github/workflows/deploy.yml`，需要設定以下 Secrets：
- `DEPLOY_HOST` — 部署主機 IP
- `DEPLOY_USER` — SSH 使用者
- `DEPLOY_SSH_KEY` — SSH 私鑰

### Docker 健康檢查

雙層健康檢查確保服務可靠：

**後端 API**: 每 30 秒驗證 `/health` + `/api/v1/orders/count`
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD python3 /healthcheck.py
```

**前端 Nginx**: 每 30 秒驗證首頁可達
```yaml
healthcheck:
  test: ["CMD", "wget", "-qO-", "http://localhost:8030/"]
```

## 技術棧

| 層級 | 技術 |
|------|------|
| 後端 | FastAPI + SQLAlchemy + SQLite |
| 前端 | React 18 + Vite + TailwindCSS + React Router |
| 圖表 | Recharts（甘特圖）|
| 日期 | date-fns |

## License

MIT
