# HTML 簡報素材庫 — 分析基準

> 任務：Allen 2026-05-25 — 從四個標竿來源建立 HTML 簡報素材庫
> 產出：完整分析報告 + structured index + design tokens 庫 + GitHub 提交

---

## 四大來源摘要

| # | 來源 | 類型 | 規模 | 適合度 |
|---|------|------|------|:--:|
| 1 | beautiful-html-templates | Reveal.js 簡報模板 | 34 套 | ⭐⭐⭐⭐⭐ |
| 2 | nicepage.com | 通用 HTML 網頁模板 | 15,000+ | ⭐⭐⭐ |
| 3 | slides.com/templates | Reveal.js 簡報市集 | ~100+ | ⭐⭐⭐⭐ |
| 4 | slides.com/explore | 社群公開簡報 | 不定 | ⭐⭐⭐ |

---

## 分析維度

每套模板分析以下項目：

### Design System
- Color palette（主色、輔色、背景色、強調色）
- Typography（字體家族、層級、字重、行高）
- Spacing system（padding/margin rhythm）
- Visual vocabulary（裝飾元素語彙）

### Layout
- Cover slide 結構
- Content slide 結構
- Section divider
- 數據展示模式
- 圖文混排模式

### 情緒/場合
- mood · tone · formality · best_for · density

### 可萃取素材
- CSS variables / design tokens
- 組件模式（card、grid、hero、timeline）
- 動畫/過場效果
- 配色方案

---

## 素材庫目錄結構

```
presentation-materials/
├── README.md                           # 使用手冊
├── index.json                          # 全班素材索引
├── templates-index/                    # 模板索引（依 mood/tone 分類）
│   ├── beautiful-html-templates.json   # source #1
│   ├── nicepage-templates.json         # source #2
│   └── slides-com-templates.json       # source #3/#4
├── design-tokens/                      # 可復用 design tokens
│   ├── color-palettes.json             # 所有配色方案
│   ├── typography-pairings.json        # 字體配對
│   └── spacing-systems.json            # 間距系統
├── color-palettes/                     # 視覺化色票
├── benchmark-analysis/                 # 標竿分析報告
│   ├── beautiful-html-templates.md     # source #1 完整分析
│   ├── nicepage-analysis.md            # source #2 分析
│   └── slides-com-analysis.md          # source #3/#4 分析
└── layouts/                            # 佈局模式目錄
```

---

## 分析進度

| Source | 狀態 | 負責 |
|--------|:--:|------|
| beautiful-html-templates | 🔄 分析中 | Christopher |
| nicepage.com | ⬜ 待分析 | — |
| slides.com/templates | ⬜ 待分析（需 browser） | — |
| slides.com/explore | ⬜ 待分析（需 browser） | — |