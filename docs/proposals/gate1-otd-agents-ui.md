# Gate 1 正式提案：OTD Agents UI 強化

**Proposer:** Vision (CRIS SWAT · 前端設計工程師)
**Date:** 2026-05-22
**Status:** In Review

---

## 1. Scope

Agent Detail Panel + 狀態指示燈 + Task Queue 三態視圖 + Filter/Sort Bar + Execution Log + GIT_COMMIT parity

以 :8040/agents 現有端點為基礎，擴充 Agent 操作管理介面，涵蓋六個交付區塊：

| # | 區塊 | 說明 |
|---|------|------|
| 1 | Agent Detail Panel | 點擊展開 Agent 身份/能力/統計資訊 |
| 2 | 狀態指示燈 | idle / working / error 三色即時狀態 |
| 3 | Task Queue 三態視圖 | pending / running / done 分頁 |
| 4 | Filter/Sort Bar | 按 agent / status / type 篩選排序 |
| 5 | Execution Log | TAO streaming log 可視化 |
| 6 | GIT_COMMIT | Docker build 時注入，/health endpoint 回傳 |

---

## 2. 標竿對照（三層疊加）

### A. ERP 業務層 — Odoo Order-to-Cash
- **標竿元素:** Odoo O2C 流程 UI — 模組化卡片、狀態流轉、可展開 Panel
- **映射:** Agent Detail Panel 採用 Odoo 卡片式展開，狀態流提示對應 Odoo workflow transitions

### B. Agent 互動層 — Linear Kanban + CrewAI Studio
- **標竿元素:** Linear Kanban Board（卡片拖放、detail panel、filter bar）+ CrewAI Studio TAO streaming
- **映射:** Task Queue 三態視圖 (pending/running/done) 對應 Linear board columns；Execution Log 對應 CrewAI Studio streaming output

### C. 操作體驗層 — Filter/Command Menu + LangSmith Trace
- **標竿元素:** Linear command menu (⌘K) + LangSmith trace 可視化
- **映射:** Filter/Sort Bar 對應 Linear filter menu；Execution Log 對應 LangSmith trace panel

---

## 3. Acceptance Criteria

| # | AC | 驗證方式 |
|---|-----|---------|
| AC1 | Agent 點擊展開 Detail Panel（identity/profile/capability/stats） | Screenshot + DOM 檢查 |
| AC2 | 狀態指示燈（idle=綠/working=安柏/error=紅）即時更新 | Screenshot + 模擬按鈕 |
| AC3 | Task Queue 三態視圖切換（pending/running/done） | Screenshot × 3 |
| AC4 | Filter/Sort Bar（by agent/status/type） | 功能測試 |
| AC5 | Execution Log TAO streaming（💭→🎯→👁️） | 截圖 + curl |
| AC6 | curl :8040/health → 200 + GIT_COMMIT 非 "unknown" | curl |

---

## 4. 交付物

1. `Agent Detail Panel` — React component, 展開/收合動畫
2. `StatusIndicator` — idle/working/error 三色指示燈 + pulse animation
3. `TaskQueueTabs` — pending/running/done 三態分頁
4. `FilterSortBar` — by agent name/status/task type 篩選
5. `ExecutionLog` — TAO streaming (💭Thought → 🎯Action → 👁️Observation)
6. `GIT_COMMIT` — Dockerfile build arg injection → :8040/health

---

## 5. Timeline

**預估：4.25 小時**

| Phase | 工作 | 時間 |
|-------|------|------|
| Spec | Detail Panel + Task Queue 規格 | 0.5h |
| Dev | 6 組件實作 | 2.5h |
| Integrate | 整合 :8040 API + TAO streaming | 0.5h |
| QA | Screenshot × 8 + curl verify | 0.5h |
| Deploy | Docker build + GIT_COMMIT + verify | 0.25h |

---

## 6. 驗收方式

```bash
# Health + GIT_COMMIT
curl -s http://100.107.36.80:8040/health | jq .commit

# Agents endpoint
curl -s http://100.107.36.80:8040/agents | jq '.[0].status'

# Screenshots
# - Agent Detail Panel（展開狀態）
# - 狀態指示燈 × 3（idle / working / error）
# - Task Queue 三態（pending / running / done）
# - Filter/Sort Bar 操作
# - Execution Log TAO streaming
```

---

## 參考

- Gate 0: recommendations/gate0-benchmark-otd.md（Vision）
- Gate 0: gate0-otd.md（Vesper）
- Gate 0: gate0-otd-forge.md（Forge）
- Commander-D: OTD 三層標竿補強（ERP/Odoo + Agent/CrewAI + UX/Linear）