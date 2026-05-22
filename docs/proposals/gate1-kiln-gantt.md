# Gate 1 正式提案：排爐系統 Gantt 互動強化

**Proposer:** Vision (CRIS SWAT · 前端設計工程師)
**Date:** 2026-05-22
**Status:** In Review

---

## 1. Scope

Gantt 拖曳互動 + 相依性連線 + 時間軸縮放 + 生命週期狀態機 transition validation + GIT_COMMIT parity

以現有 `/gantt` 甘特圖頁面為基礎，從靜態可視化升級為全互動排程操作面板：

| # | 區塊 | 說明 |
|---|------|------|
| 1 | Gantt 拖曳互動 | 拖曳調整爐次排程順序 |
| 2 | 相依性連線 | SVG 箭頭線顯示模具→爐次依賴關係 |
| 3 | 時間軸縮放 | 日/週/月三級縮放，現有 VIEW_MODES 擴充 |
| 4 | 生命週期狀態機 | pending → scheduled → running → done 四態 transition 驗證 |
| 5 | GIT_COMMIT parity | Docker build 注入 commit hash，:8030/health 回傳 |

---

## 2. 標竿對照

### A. Asana Timeline
- **標竿元素:** 拖曳排程 bar、相依性連線箭頭、多層縮放（天/週/月/季）
- **映射:** Gantt 拖曳 + 相依線 + 縮放對應 Asana Timeline 三核心

### B. Notion Calendar
- **標竿元素:** 行事曆視圖、拖放事件、多視圖切換（日/週/月/時間軸）
- **映射:** 時間軸縮放對應 Notion Calendar 視圖層級切換

### C. Linear Method
- **標竿元素:** 生命週期狀態機、transition rules、status 驗證
- **映射:** 排產狀態機 (pending→scheduled→running→done) 對應 Linear issue lifecycle

---

## 3. Acceptance Criteria

| # | AC | 驗證方式 |
|---|-----|---------|
| AC1 | Gantt bar 可拖曳調整 deliver_date | Screenshot + drag test |
| AC2 | 相依性連線箭頭從模具指向排程爐次 | Screenshot + DOM SVG 檢查 |
| AC3 | 時間軸縮放日/週/月（現有 VIEW_MODES 擴充） | Screenshot × 3 |
| AC4 | 狀態機 transition 驗證（非法跳轉攔截） | 功能測試 + console assert |
| AC5 | curl :8030/health → 200 + GIT_COMMIT 非 "unknown" | curl |
| AC6 | 8 routes 全 200 | curl loop |

---

## 4. 交付物

1. `GanttDrag` — 拖曳互動（react-dnd 或 pointer events）
2. `DependencyLines` — SVG overlay 箭頭連線層
3. `TimeScaleZoom` — 日/週/月縮放控制項（整合 VIEW_MODES）
4. `StatusMachine` — 狀態機 transition validation（pending→scheduled→running→done）
5. `GIT_COMMIT` — Dockerfile build arg → :8030/health
6. Deploy — docker compose up -d --build + 8 route smoke test

---

## 5. Timeline

**預估：4.5 小時**

| Phase | 工作 | 時間 |
|-------|------|------|
| Spec | 拖曳 + 相依線 + 狀態機設計 | 0.5h |
| Dev 1 | Gantt 拖曳 + 相依連線 | 2h |
| Dev 2 | 縮放 + 狀態機 transition | 1h |
| Integrate | 整合後端 API + transition rules | 0.5h |
| QA | Screenshot × 6 + curl 8 routes | 0.25h |
| Deploy | Docker build + smoke test | 0.25h |

---

## 6. 驗收方式

```bash
# Health + GIT_COMMIT
curl -s http://100.107.36.80:8030/health | jq .commit

# 8 routes 全 200
for r in / /health /orders /molds /schedule /gantt /reports /settings; do
  echo -n "$r: "; curl -sSo/dev/null -w "%{http_code}" "http://100.107.36.80:8030$r"; echo
done

# Screenshots
# - Gantt 拖曳前後對比（drag start → drag end）
# - 相依性連線 SVG（箭頭層疊在甘特圖上）
# - 時間軸縮放 × 3（日/週/月）
# - 狀態機 transition diagram + 非法跳轉攔截 console
```

---

## 參考

- Gate 0: recommendations/gate0-benchmark-kiln.md（Vision）
- Gate 0: gate0-furnace.md（Vesper）
- Gate 0: gate0-furnace-forge.md（Forge）