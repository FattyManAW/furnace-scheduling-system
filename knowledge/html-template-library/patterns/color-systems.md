# 配色系統（10 套）

> 跨 4 來源萃取 · CSS Custom Properties 格式

## 套用方式
```html
<link rel="stylesheet" href="color-systems.css">
<!-- 在 <body> 加 class 選擇配色 -->
<body class="palette-editorial-forest">
```

## 01 editorial-forest（商務 · 深綠）
```css
.palette-editorial-forest {
  --c-primary: #2d5a3d;      /* 森林綠 */
  --c-secondary: #d4a5a5;    /* 塵粉 */
  --c-accent: #f0c040;       /* 暖黃 accent */
  --c-bg: #faf8f5;           /* 暖奶油紙色 */
  --c-text: #2c2c2c;         /* 深灰文字 */
  --c-text-muted: #6b6b6b;   /* 次要文字 */
  --c-border: #e0ddd5;       /* 極細邊框 */
  --c-card: #ffffff;         /* 卡片白 */
}
```
適用：P0 用友商務簡報 · 季度審查 · 策略報告

## 02 cobalt-grid（科技 · 藍調）
```css
.palette-cobalt-grid {
  --c-primary: #2563EB;      /* 電光鈷藍 */
  --c-secondary: #1E293B;    /* 暗灰 */
  --c-accent: #F59E0B;       /* 橙 */
  --c-bg: #F8FAFC;           /* 圖紙灰 */
  --c-text: #0F172A;         /* 深黑文字 */
  --c-text-muted: #64748B;   /* 次要文字 */
  --c-border: #E2E8F0;       /* 細框 */
  --c-card: #FFFFFF;         /* 卡片白 */
}
```
適用：P3 CRIS 碳足跡 · 數據分析 · 技術簡報

## 03 neo-grid-bold（Neo-brutalism）
```css
.palette-neo-grid-bold {
  --c-primary: #000000;      /* 純黑 */
  --c-secondary: #F5F5F0;    /* 米白紙 */
  --c-accent: #FFE600;       /* 螢光黃 */
  --c-bg: #FAFAF5;           /* 米白底 */
  --c-text: #1A1A1A;         /* 近黑 */
  --c-text-muted: #666666;   /* 灰 */
  --c-border: #000000;       /* 粗黑邊框 */
  --c-card: #FFFFFF;         /* 卡片白 */
}
```
適用：Kanban 看板 · 創意提案 · 品牌簡報

## 04 metric-dashboard（KPI · 儀表板）
```css
.palette-metric-dashboard {
  --c-primary: #1E3A5F;      /* 深藍 */
  --c-secondary: #F8F9FA;    /* 淺灰 */
  --c-accent-up: #10B981;    /* 綠(↑) */
  --c-accent-down: #EF4444;  /* 紅(↓) */
  --c-bg: #F1F5F9;           /* 藍灰底 */
  --c-text: #0F172A;         /* 深黑 */
  --c-text-muted: #64748B;   /* 灰 */
  --c-border: #E2E8F0;       /* 框 */
  --c-card: #FFFFFF;         /* 卡片 */
}
```
適用：OTD Dashboard · KPI 報告 · 數據儀表板

## 05 emerald-editorial（雜誌封面 · 翡翠）
```css
.palette-emerald-editorial {
  --c-primary: #065F46;      /* 翡翠綠 */
  --c-secondary: #1E3A5F;    /* 海軍藍 */
  --c-accent: #D4AF37;       /* 金 */
  --c-bg: #FFFBEB;           /* 暖紙色 */
  --c-text: #1A1A1A;         /* 深黑 */
  --c-text-muted: #6B7280;   /* 灰 */
  --c-border: #D1D5DB;       /* 框 */
  --c-card: #FFFFFF;         /* 白卡片 */
}
```
適用：投資人簡報 · 品牌書 · 年度報告

## 06 sakura-chroma（日式復古 · 彩虹）
```css
.palette-sakura-chroma {
  --c-primary: #DC2626;      /* 朱紅 */
  --c-secondary: #F5F0E8;    /* 奶油紙 */
  --c-accent-1: #2563EB;     /* 藍 */
  --c-accent-2: #F59E0B;     /* 黃 */
  --c-accent-3: #10B981;     /* 綠 */
  --c-bg: #FFFDF5;           /* 暖白底 */
  --c-text: #1A1A1A;         /* 深黑 */
  --c-text-muted: #6B7280;   /* 灰 */
  --c-border: #E5E0D5;       /* 框 */
}
```
適用：亞洲市場 · 創意提案 · 產品發布

## 07 midnight-blue（暗色模式）
```css
.palette-midnight-blue {
  --c-primary: #1E293B;      /* 午夜藍 */
  --c-secondary: #334155;    /* 石板灰 */
  --c-accent: #38BDF8;       /* 天藍 accent */
  --c-bg: #0F172A;           /* 深黑藍底 */
  --c-text: #F1F5F9;         /* 淺灰文字 */
  --c-text-muted: #94A3B8;   /* 次要 */
  --c-border: #334155;       /* 框 */
  --c-card: #1E293B;         /* 卡片 */
}
```
適用：科幻/技術 · 夜間演示 · 暗色主題

## 08 soft-editorial（柔和 · 溫暖）
```css
.palette-soft-editorial {
  --c-primary: #84A98C;      /* 鼠尾草綠 */
  --c-secondary: #D4A5A5;    /* 腮紅粉 */
  --c-accent: #F0C040;       /* 檸檬黃 */
  --c-bg: #FAF8F5;           /* 暖白 */
  --c-text: #2C2C2C;         /* 深灰 */
  --c-text-muted: #8B8B8B;   /* 灰 */
  --c-border: #E0DDD5;       /* 極細框 */
  --c-card: #FFFFFF;         /* 卡片白 */
}
```
適用：內部匯報 · 人文主題 · 溫暖品牌

## 09 gradient-play（新創 pitch · 紫→藍）
```css
.palette-gradient-play {
  --c-gradient: linear-gradient(135deg, #7C3AED 0%, #2563EB 100%);
  --c-primary: #7C3AED;      /* 紫 */
  --c-secondary: #2563EB;    /* 藍 */
  --c-accent: #F59E0B;       /* 黃 */
  --c-bg: #FFFFFF;           /* 白底 */
  --c-text: #1A1A1A;         /* 深黑 */
  --c-text-muted: #6B7280;   /* 灰 */
  --c-border: #E2E8F0;       /* 框 */
  --c-card: #F8FAFC;         /* 淺灰卡片 */
}
```
適用：新創 pitch · 產品發布 · 品牌活動

## 10 duotone-bold（雙色調 · 高對比）
```css
.palette-duotone-bold {
  --c-primary: #E11D48;      /* 玫瑰紅 */
  --c-secondary: #0F172A;    /* 深黑 */
  --c-accent: #FACC15;       /* 亮黃 */
  --c-bg: #0F172A;           /* 深黑底 */
  --c-text: #F8FAFC;         /* 白字 */
  --c-text-muted: #94A3B8;   /* 灰 */
  --c-border: #334155;       /* 框 */
  --c-card: #1E293B;         /* 暗卡片 */
}
```
適用：品牌活動 · 高衝擊 · 廣告提案

## 配色決策樹

```
用途？
├─ 商務/客戶 → editorial-forest · emerald-editorial
├─ 科技/數據 → cobalt-grid · metric-dashboard
├─ 創意/品牌 → neo-grid-bold · gradient-play
├─ 內部匯報 → soft-editorial
├─ 暗色演示 → midnight-blue · duotone-bold
└─ 亞洲市場 → sakura-chroma
```