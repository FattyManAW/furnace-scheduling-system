# Deploy Checklist — 乾式套管最佳化排爐系統

_建立日期：2026-05-25 | 作者：Vesper | 實戰驗證_

每次 `docker compose up -d --build` 前，逐項確認。

---

## Phase 0 — 部署前（Code）

- [ ] **Code changes committed** — `git status` 乾淨
- [ ] **`git pull` 成功** — 若卡 HTTPS timeout：用 `git fetch` → `git merge` 分步
- [ ] **Dockerfile `COPY` 含所有子目錄** — 若加了新檔案/目錄，確認 Dockerfile `COPY` 語句涵蓋

---

## Phase 1 — Build 前

- [ ] **`GIT_COMMIT` env 有值** — Dockerfile `ARG GIT_COMMIT` 需要 build-time env
  ```bash
  export GIT_COMMIT=$(git rev-parse --short HEAD)
  ```
  - ❌ 沒帶 env → commit=unknown
  - ✅ `export GIT_COMMIT=<hash> && docker compose up -d --build`

---

## Phase 2 — Build & Deploy

- [ ] **Build with env**
  ```bash
  export GIT_COMMIT=$(git rev-parse --short HEAD)
  docker compose up -d --build
  ```
- [ ] **Docker healthcheck 確認** — 容器 HEALTHCHECK path 對應實際 endpoint
  - ✅ `test: ["CMD", "python3", "/healthcheck.py"]`
- [ ] **npm build 若適用**
  ```bash
  npm --prefix frontend run build
  docker compose up -d --build nginx
  ```

---

## Phase 3 — Verify（部署後）

- [ ] **容器狀態 healthy** — `docker ps | grep furnace-api | grep healthy`
- [ ] **`/health` → 200**
  ```bash
  curl -sS http://100.107.36.80:8002/health
  # {"status":"ok","commit":"<hash>","version":"2.0.0"}
  ```
- [ ] **GIT_COMMIT 匹配**
  ```bash
  curl -sS http://100.107.36.80:8002/health | jq -r .commit
  # 必須等於 git rev-parse --short HEAD
  ```
- [ ] **8+ routes 全 200**
  | Endpoint | Method | 預期 |
  |----------|--------|------|
  | /health | GET | 200 |
  | / | GET | 200 (:8030 UI) |
  | /api/furnace/ | GET | 200 |
  | /api/furnace/schedule | POST | 200 |
  | /api/orders | GET | 200 |
  | /api/orders/{id} | GET | 200 |
  | /api/molds | GET | 200 |
  | /api/gantt | GET | 200 |
  | /docs | GET | 200 |

---

## Phase 4 — 驗收（Production Check）

- [ ] **curl deploy-verify.json**（若存在於 frontend）
- [ ] **3 次 health check 連續 200**（排除 transient error）
- [ ] **Browser 驗證** — 手動開啟 :8030 確認 UI 可互動

---

## 常見故障排除

| 症狀 | 根因 | 解法 |
|------|------|------|
| `commit=unknown` | 未 export GIT_COMMIT | `export GIT_COMMIT=$(git rev-parse --short HEAD)` |
| nginx 403 | dist/ file perms | `docker compose exec nginx chmod -R 755 /usr/share/nginx/html/` |
| API 連不到 | Docker network | `docker compose-down && docker compose up -d` |
| docker compose 0 bytes | 檔案被清空 | `git show <commit>:docker-compose.yml > docker-compose.yml` |
| GitHub HTTPS timeout | port 443 間歇 | `GIT_HTTP_LOW_SPEED_LIMIT=1000` 或改用 gh CLI |

---

*最後更新：2026-05-25 | 驗證週期：每次部署前重新 review*
