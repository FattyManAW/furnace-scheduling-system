# nicepage Design Patterns — 簡報適用型萃取

> Source #2 · 協作：Wendy（篩選） + Christopher（技術萃取）
> Wendy 已標 P0 區塊：Features Grid · Split · Shapes · Grid Repeater · Slider

---

## 技術限制

nicepage.com 全站 JS 渲染（web_fetch 只拿到框架文字，無實際 CSS/HTML）。無法用 extract_tokens.py 直接萃取。改採推導式分析：從 nicepage 已知技術棧（Bootstrap 5 + CSS Grid + Flexbox + CSS Custom Properties）反向建模適用於簡報的 design tokens。

---

## P0 區塊：簡報適用 CSS 模式

### 1. Features Grid（@npg- 命名空間）

```css
/* nicepage Features Grid → 簡報適用 */
.npg-features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  padding: 4rem 2rem;
}

.npg-feature-card {
  background: var(--npg-surface);
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.npg-feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

.npg-feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.npg-feature-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.npg-feature-desc {
  font-size: 0.95rem;
  color: var(--npg-text-secondary);
  line-height: 1.6;
}

/* 簡報適用：3-column fixed */
.npg-presentation-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}
```

### 2. Split Layout（Hero 簡報模式）

```css
.npg-split-hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 60vh;
  align-items: center;
  gap: 3rem;
  padding: 2rem 4rem;
}

.npg-split-hero.reversed {
  direction: rtl;
}

.npg-split-hero.reversed > * {
  direction: ltr;
}

.npg-split-text {
  max-width: 560px;
}

.npg-split-text h1 {
  font-size: clamp(2rem, 5vw, 3.5rem);
  line-height: 1.15;
  margin-bottom: 1.5rem;
}

.npg-split-text p {
  font-size: 1.15rem;
  line-height: 1.7;
  color: var(--npg-text-secondary);
  margin-bottom: 2rem;
}

.npg-split-visual {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 簡報變體：Hero Number */
.npg-hero-number {
  font-size: clamp(4rem, 8vw, 7rem);
  font-weight: 800;
  line-height: 1;
  background: var(--npg-gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### 3. Decorative Shapes（裝飾元件）

```css
.npg-shape-circle {
  width: 120px; height: 120px;
  border-radius: 50%;
  background: var(--npg-accent);
  opacity: 0.15;
  position: absolute;
}

.npg-shape-blob {
  border-radius: 60% 40% 50% 45% / 55% 45% 55% 45%;
  animation: npg-blob-morph 8s ease-in-out infinite;
}

@keyframes npg-blob-morph {
  0%, 100% { border-radius: 60% 40% 50% 45% / 55% 45% 55% 45%; }
  33% { border-radius: 45% 55% 40% 60% / 50% 60% 45% 55%; }
  66% { border-radius: 55% 40% 60% 50% / 40% 55% 45% 60%; }
}

.npg-shape-accent-bar {
  width: 60px; height: 4px;
  background: var(--npg-accent);
  border-radius: 2px;
  margin-bottom: 1.5rem;
}
```

### 4. Grid Repeater（動態網格）

```css
.npg-grid-repeater {
  display: grid;
  grid-template-columns: repeat(var(--npg-cols, 4), 1fr);
  gap: var(--npg-gap, 1.5rem);
}

.npg-grid-repeater .npg-cell {
  aspect-ratio: 1;
  background: var(--npg-surface);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.npg-grid-repeater .npg-cell:hover {
  background: var(--npg-accent);
  color: white;
  transform: scale(1.05);
}
```

### 5. Slider / Carousel（卡片輪播）

```css
.npg-slider-track {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  gap: 1.5rem;
  padding: 1rem 0;
  scrollbar-width: none;
}

.npg-slider-card {
  flex: 0 0 320px;
  scroll-snap-align: start;
  background: var(--npg-surface);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
```

---

## 19 產業色彩系統映射

基於 Wendy 的 19 產業分類，建立簡報適用調色板：

| 產業 | Primary | Secondary | Accent | Surface | 風格 |
|------|---------|-----------|--------|---------|------|
| Finance | #1A365D | #2B6CB0 | #ECC94B | #F7FAFC | 穩重專業 |
| Tech/SaaS | #6B46C1 | #805AD5 | #00E5FF | #0A0E27 | 未來感 |
| Healthcare | #276749 | #38A169 | #F6AD55 | #F0FFF4 | 信賴溫暖 |
| Education | #C05621 | #DD6B20 | #3182CE | #FFFAF0 | 活力學習 |
| Real Estate | #2D3748 | #4A5568 | #48BB78 | #F7FAFC | 現代可靠 |
| Creative | #E53E3E | #FC8181 | #F6E05E | #1A202C | 大膽對比 |
| E-commerce | #2B6CB0 | #3182CE | #F56565 | #EBF8FF | 行動導向 |
| Corporate | #1A202C | #2D3748 | #3182CE | #FFFFFF | 極簡專業 |
| Nonprofit | #2F855A | #48BB78 | #F6AD55 | #F0FFF4 | 溫暖使命 |
| Fashion | #97266D | #D53F8C | #000000 | #FAF5FF | 奢華精緻 |
| Food | #C05621 | #ED8936 | #38A169 | #FFFAF0 | 食慾溫暖 |
| Travel | #2B6CB0 | #63B3ED | #F6AD55 | #EBF8FF | 探索開放 |
| Construction | #744210 | #975A16 | #3182CE | #FFFFF0 | 堅固信賴 |
| Legal | #1A365D | #2A4365 | #C53030 | #F7FAFC | 權威嚴肅 |
| Media | #2D3748 | #4A5568 | #E53E3E | #1A202C | 編輯現代 |
| Fitness | #2F855A | #48BB78 | #E53E3E | #F0FFF4 | 活力動感 |
| Beauty | #97266D | #ED64A6 | #F6E05E | #FFFAF0 | 柔和女性 |
| Automotive | #1A202C | #2D3748 | #E53E3E | #F7FAFC | 力量精準 |
| Generic | #3182CE | #63B3ED | #48BB78 | #FFFFFF | 中性通用 |

---

## 字體配對系統

從 nicepage 常見模式推導：

```css
/* 簡報字體配對 — nicepage-inspired */
:root {
  /* Pairing 1: Modern Geometric */
  --npg-font-geo-heading: 'Montserrat', 'Noto Sans TC', sans-serif;
  --npg-font-geo-body: 'Inter', 'Noto Sans TC', sans-serif;

  /* Pairing 2: Editorial Classic */
  --npg-font-editorial-heading: 'Playfair Display', 'Noto Serif TC', serif;
  --npg-font-editorial-body: 'Lora', 'Noto Serif TC', serif;

  /* Pairing 3: Tech Sans */
  --npg-font-tech-heading: 'Space Grotesk', 'Noto Sans TC', sans-serif;
  --npg-font-tech-body: 'IBM Plex Sans', 'Noto Sans TC', sans-serif;

  /* Pairing 4: Corporate Clean */
  --npg-font-corp-heading: 'Poppins', 'Noto Sans TC', sans-serif;
  --npg-font-corp-body: 'Open Sans', 'Noto Sans TC', sans-serif;

  /* Pairing 5: Warm Humanist */
  --npg-font-warm-heading: 'Crimson Text', 'Noto Serif TC', serif;
  --npg-font-warm-body: 'Nunito', 'Noto Sans TC', sans-serif;

  /* Pairing 6: Mono Technical */
  --npg-font-mono-heading: 'JetBrains Mono', 'Noto Sans TC', monospace;
  --npg-font-mono-body: 'Fira Code', monospace;
}

/* 字級階層（nicepage scale） */
.npg-scale-hero    { font-size: clamp(2.5rem, 6vw, 4.5rem); }
.npg-scale-h1      { font-size: clamp(2rem, 4vw, 3rem); }
.npg-scale-h2      { font-size: clamp(1.5rem, 3vw, 2rem); }
.npg-scale-h3      { font-size: 1.25rem; }
.npg-scale-body    { font-size: 1rem; line-height: 1.7; }
.npg-scale-caption { font-size: 0.875rem; color: var(--npg-text-muted); }
```

---

## 匯出：簡報適用 reusable CSS

完整檔案路徑：`patterns/nicepage-presentation-patterns.css`

- 5 P0 區塊佈局（Features Grid · Split · Shapes · Repeater · Slider）
- 19 產業色彩系統（CSS Custom Properties）
- 6 字體配對 + 字級階層
- 簡報專用 utilities（hero-number、accent-bar、section-marker）