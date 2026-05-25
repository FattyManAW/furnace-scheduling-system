# Slides.com — 簡報素材庫分析報告

> Source #4 · 負責：Christopher · 日期：2026-05-25

---

## 來源摘要

| 屬性 | 值 |
|------|------|
| **URL** | https://slides.com/explore |
| **類型** | Reveal.js 社群公開簡報庫 |
| **存取方式** | JS SPA（需 browser render）|
| **授權** | 各簡報作者自訂（非統一模板授權）|
| **適合用途** | 設計靈感參考、佈局模式研究、色彩搭配觀察 |
| **不適合用途** | 直接複製使用、模板 clone 後改內容 |

---

## 技術障礙

slides.com 是全端 JS SPA，依賴 client-side rendering：

- `web_fetch` → timeout（無 SSR，HTML 空殼）
- `curl` → 空回應
- `browser` → CDP timeout（Mac 環境限制）

## 已知結構（基於公開資訊）

slides.com/explore 的類別結構：

| 類別 | 描述 | 素材價值 |
|------|------|:--:|
| Technology | 科技產品/新創 pitch | ⭐⭐⭐⭐ |
| Business | 商業簡報/財報 | ⭐⭐⭐⭐ |
| Education | 教學/課程 | ⭐⭐⭐ |
| Design | 設計作品集 | ⭐⭐⭐⭐⭐ |
| Marketing | 行銷活動 | ⭐⭐⭐ |
| Science | 學術研究 | ⭐⭐ |

## 與其他來源的互補性

| 來源 | 優勢 | slides.com/explore 的補充 |
|------|------|------|
| beautiful-html-templates | 34 套可 clone 模板 | 真實使用案例（非模板 demo 內容）|
| nicepage.com | 15,000+ 網頁模板 | 簡報專用（非通用網頁）|
| slides.com/templates | 付費模板市集 | 免費公開作品 |

---

## 建議後續行動

1. **Browser-based exploration**（需 human 或 browser node）：
   - 開啟 slides.com/explore → 瀏覽 Top/Featured
   - 每類別截圖 3-5 個代表性作品
   - 記錄使用的 Reveal.js 主題、過場、佈局模式

2. **API scraping**（若 slides.com 提供公開 API）：
   - 檢查 `slides.com/api/explore` 是否有 JSON endpoint
   - 如有，批次抓取 metadata（title、author、category、theme）

3. **Reveal.js 主題分析**：
   - 從公開作品反推常用的 Reveal.js themes（black/white/league/beige/sky/night/serif/simple/solarized）
   - 記錄自訂主題的 CSS 模式

---

## 可萃取素材（推估）

| 素材類型 | 推估數量 | 萃取方式 |
|----------|:--:|------|
| 佈局模式 | 50+ | 截圖分析 |
| 色彩搭配 | 100+ | 視覺取樣 |
| 動畫/過場 | 20+ | 互動觀察 |
| 資料視覺化 | 30+ | 截圖標記 |
| 字體配對 | 40+ | 瀏覽器 DevTools |

---

## 結論

slides.com/explore 是很好的**靈感參考**來源，但不適合作為可直接 clone 的模板庫。建議優先完成 #1（beautiful-html-templates）+ #2（nicepage design tokens），最後用 #4 做 cross-reference 驗證素材庫的覆蓋度。