# 字體配對（10 套）

> 跨 4 來源萃取 · Google Fonts @import 格式 · 含中文對應

## 配對原則
- **Display（標題）** + **Body（內文）** + **Mono（數據）**
- 中文字體：Noto Sans TC / Noto Serif TC
- 所有組合都測試過中西文混排

## 配對 01：編輯經典
```css
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Source+Serif+4:opsz,wght@8..60,300;8..60,400&display=swap');
.pairing-editorial-classic {
  --f-display: 'Cormorant Garamond', 'Noto Serif TC', serif;
  --f-body: 'Source Serif 4', 'Noto Serif TC', serif;
  --f-mono: 'JetBrains Mono', monospace;
}
```
來源：soft-editorial · editorial-forest · vellum（6 模板）

## 配對 02：現代科技
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=DM+Sans:wght@400;500;700&display=swap');
.pairing-modern-tech {
  --f-display: 'DM Sans', 'Noto Sans TC', sans-serif;
  --f-body: 'Inter', 'Noto Sans TC', sans-serif;
  --f-mono: 'JetBrains Mono', monospace;
}
```
來源：cobalt-grid · metric-dashboard · midnight-blue（5 模板）

## 配對 03：Neo-Brutalism
```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;600&display=swap');
.pairing-neo-brutalist {
  --f-display: 'Space Grotesk', 'Noto Sans TC', sans-serif;
  --f-body: 'Inter', 'Noto Sans TC', sans-serif;
  --f-mono: 'DM Mono', monospace;
}
```
來源：neo-grid-bold · brutalist-raw（2 模板）

## 配對 04：溫暖人文
```css
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');
.pairing-warm-human {
  --f-display: 'Playfair Display', 'Noto Serif TC', serif;
  --f-body: 'Lora', 'Noto Serif TC', serif;
  --f-mono: 'Source Code Pro', monospace;
}
```
來源：soft-editorial · pin-and-paper（3 模板）

## 配對 05：極簡 Swiss
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700&family=Noto+Sans:wght@300;400;600&display=swap');
.pairing-swiss-minimal {
  --f-display: 'Inter', 'Noto Sans TC', sans-serif;
  --f-body: 'Noto Sans', 'Noto Sans TC', sans-serif;
  --f-mono: 'JetBrains Mono', monospace;
}
```
來源：zen-white · airy-spaces · single-column（3 模板）

## 配對 06：企業專業
```css
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&family=Roboto:wght@300;400;500&display=swap');
.pairing-corporate {
  --f-display: 'Lato', 'Noto Sans TC', sans-serif;
  --f-body: 'Roboto', 'Noto Sans TC', sans-serif;
  --f-mono: 'Roboto Mono', monospace;
}
```
來源：navy-corporate · trust-blue · steel-gray（4 模板）

## 配對 07：新創活潑
```css
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&family=Nunito:wght@300;400;600&display=swap');
.pairing-startup-vibrant {
  --f-display: 'Poppins', 'Noto Sans TC', sans-serif;
  --f-body: 'Nunito', 'Noto Sans TC', sans-serif;
  --f-mono: 'Fira Code', monospace;
}
```
來源：gradient-play · color-pop（3 模板）

## 配對 08：數據分析
```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
.pairing-data-analytics {
  --f-display: 'IBM Plex Sans', 'Noto Sans TC', sans-serif;
  --f-body: 'IBM Plex Sans', 'Noto Sans TC', sans-serif;
  --f-mono: 'IBM Plex Mono', monospace;
}
```
來源：metric-dashboard · data-dense · table-minimal（4 模板）

## 配對 09：日式簡約
```css
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&family=Noto+Sans+TC:wght@300;400;700&display=swap');
.pairing-japanese-minimal {
  --f-display: 'Noto Sans JP', 'Noto Sans TC', sans-serif;
  --f-body: 'Noto Sans TC', sans-serif;
  --f-mono: 'Source Code Pro', monospace;
}
```
來源：sakura-chroma · 日系設計

## 配對 10：大標題 Display
```css
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,700;6..96,900&family=Source+Sans+3:wght@300;400;600&display=swap');
.pairing-display-bold {
  --f-display: 'Bodoni Moda', 'Noto Serif TC', serif;
  --f-body: 'Source Sans 3', 'Noto Sans TC', sans-serif;
  --f-mono: 'JetBrains Mono', monospace;
}
```
來源：emerald-editorial（雜誌級）

## 選用指南

| 場景 | 推薦配對 |
|------|------|
| 商務客戶簡報 | 01 編輯經典 · 06 企業專業 |
| 技術/開發者 | 02 現代科技 · 08 數據分析 |
| 投資人/董事會 | 01 編輯經典 · 10 大標題 |
| 新創 pitch | 07 新創活潑 · 03 Neo-Brutalism |
| 內部工作匯報 | 04 溫暖人文 · 05 極簡 Swiss |
| 亞洲市場 | 09 日式簡約 · 04 溫暖人文 |