# 干式套管最佳化排爐系統 — 使用說明

**版本 v2.0.1** | 2026-05-19

---

## 🚀 一鍵啟動

```bash
chmod +x start.sh
./start.sh
```

腳本會自動：clone 原始碼 → 建置 Docker → 啟動後端 → 印出所有連結。

---
##  系統架構
```
      Browser（你的電腦）
           │
   ┌───────┴───────┐
   │               │
   ▼               ▼
前端 SPA          後端 API
GitHub Pages      Docker (Mac mini)
(fattymanaw       (port 8002)
.github.io)          │
                     ▼
                 SQLite DB
              (251 筆訂單)
```

---

## 📍 服務位址

| 項目 | URL |
|------|-----|
| **前端 SPA（推薦）** | https://fattymanaw.github.io/furnace-scheduling-system/ |
| 後端 API | http://100.107.36.80:8002 |
| Swagger 文件 | http://100.107.36.80:8002/docs |
| API 文件 | docs/API文件.md |

---

## 🖼️ 介面一覽

> *建議在此處放截圖：*
> - [ ] Dashboard（儀表板統計頁面）
> - [ ] Orders（訂單列表與搜尋）
> - [ ] Schedule（排程優化結果）
> - [ ] Gantt（甘特圖 — 罐位時間線）

---

## 📊 主要功能

| 功能 | 說明 |
|------|------|
| 訂單管理 | 251 筆套管生產訂單，支援搜尋/篩選/CRUD |
| 模具庫存 | 16 種模具，支援入庫/出庫/低庫存提醒 |
| 干燥罐 | 28 個干燥罐，支援方案查詢 |
| 排程優化 | 一鍵排程，deadline/fill/balance 三策略 |
| 甘特圖 | 可視化罐位時間線，1週/2週/4週視圖 |
| 報表匯出 | CSV/JSON 匯出訂單與排程結果 |

---

## 🛠️ 常見問題

### Q: 前端打開後沒有資料？
A: 確認 Mac mini Docker 正在運行（`docker ps` 看 furnace-api 是否 healthy）。確認 Tailscale 已連線。

### Q: CORS 錯誤？
A: 檢查 `ALLOWED_ORIGINS` 環境變數是否包含 `https://fattymanaw.github.io`。編輯 `.env` 後 `docker compose restart`。

### Q: 資料庫重新設定？
A: `docker compose down -v && docker compose up -d` 會清除資料庫並重新匯入種子資料。

### Q: Docker 未安裝？
A: 下載 Docker Desktop：https://docs.docker.com/get-docker/

---

## 📁 專案結構

```
furnace-scheduling-system/
├── start.sh                 # 一鍵啟動
├── Dockerfile               # Docker 建置
├── docker-compose.yml       # Docker Compose
├── .env                     # 環境變數
├── backend/                 # FastAPI 後端
│   ├── main.py
│   ├── api/                 # API routes
│   ├── engine/              # 排程引擎
│   └── tests/               # 29 個測試
├── frontend/                # React 前端
├── data/                    # 種子資料 (JSON)
└── docs/                    # 文件
    ├── API文件.md
    ├── 後端部署方案建議書.md
    └── 後端部署操作手冊.md
```