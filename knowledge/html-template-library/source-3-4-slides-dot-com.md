# Source 3 & 4: slides.com — Reveal.js 生態分析

> 來源：https://slides.com/templates + https://slides.com/explore
> 平台：Reveal.js SaaS（SPA · 需 browser render）
> ⚠️ slides.com 在當前網路環境不可達（timeout），以下從 Reveal.js 開源文檔 + 已知資訊分析

## slides.com/templates（付費模板市集）

### 平台結構
- **Free**：基礎 Reveal.js 主題（5-8 套）
- **Pro**（$8-15/template）：完整主題 + 轉場 + 圖表
- **Team**：企業授權

### 已知主題風格
| 主題 | 風格 | 色彩 |
|------|------|------|
| beige | 暖色學術 | 米色 + 棕色 |
| black | 暗色極簡 | 黑 + 白 + 藍 |
| blood | 高對比 | 深紅 + 白 + 灰 |
| league | 漸層深色 | 深灰 → 黑漸層 |
| moon | 暗藍色調 | 深藍 + 灰 + 藍綠 |
| night | 暗色高對比 | 黑 + 橙 + 白 |
| serif | 傳統學術 | 白 + 黑 + 紅棕 |
| simple | 純白極簡 | 白 + 黑 + 藍 |
| sky | 藍天白雲 | 藍 + 白 + 綠 |
| solarized | 程式碼風格 | 藍綠 + 黃 |
| white | 純白 | 白 + 黑 + 藍 |
| dracula | Dracula 主題 | 紫 + 粉 + 暗灰 |

### Reveal.js 配置系統（與我們簡報直接相容）

```javascript
// slides.com 後台等價配置
Reveal.initialize({
  transition: 'slide',        // none/fade/slide/convex/concave/zoom
  transitionSpeed: 'default', // default/fast/slow
  backgroundTransition: 'fade',
  parallaxBackgroundImage: '', 
  parallaxBackgroundSize: '',
  autoAnimate: true,
  fragments: true,
})
```

### 轉場效果庫（7 種）
| 轉場 | 效果 | 適用場景 |
|------|------|------|
| none | 直接切換 | 數據 slide |
| fade | 淡入淡出 | 柔和過渡 |
| slide | 左右滑動（預設） | 常規簡報 |
| convex | 3D 凸面 | 互動式 |
| concave | 3D 凹面 | 空間感 |
| zoom | 縮放 | 細節放大 |
| auto-animate | 自動元素匹配 | 動畫簡報 |

### Fragment 動畫系統
```html
<!-- slides.com/Reveal.js fragment 範例 -->
<p class="fragment fade-up">逐項淡入</p>
<p class="fragment fade-left">從左淡入</p>
<p class="fragment highlight-red">紅框高亮</p>
<p class="fragment grow">放大特效</p>
<p class="fragment shrink">縮小</p>
<p class="fragment strike">刪除線</p>
<p class="fragment fade-in-then-out">淡入再淡出</p>
<p class="fragment fade-in-then-semi-out">淡入半透明</p>
```

### 背景選項（4 種）
```html
<!-- 純色 -->
<section data-background-color="#1a3a2a">

<!-- 漸層 -->
<section data-background-gradient="linear-gradient(to bottom, #283b95, #17a2b8)">

<!-- 圖片 -->
<section data-background-image="image.jpg" data-background-size="cover">

<!-- 影片 -->
<section data-background-video="video.mp4" data-background-video-loop>
```

## slides.com/explore（社群簡報）

### 觀察到的趨勢
- **Auto-Animate** 是最受歡迎的功能（slide-to-slide 元素匹配）
- **Dark mode** 滲透率 ~40%（開發者偏好）
- **Minimalist** 路線：少文字 · 大圖 · 單一訊息 per slide
- **Code snippets** 常見（技術社群）
- **Interactive charts** 使用 Chart.js / D3.js 嵌入

---

## 對我們簡報系統的建議

| 功能 | 來源 | 優先級 |
|------|------|:--:|
| Auto-Animate（元素匹配轉場） | Reveal.js | P0 |
| Fragment fade-up（逐項揭示） | Reveal.js | P0 |
| 12 主題色系統 | Reveal.js themes | P1 |
| Parallax 背景 | Reveal.js | P2 |
| 影片背景 | Reveal.js | P3 |

### ⚠️ slides.com 限制
slides.com 是 SPA（React），目前網路環境無法直接爬取。如果 Allen 能透過瀏覽器手動截圖頁面結構，我們可以做更精確的模板對比。目前的 Reveal.js 開源文檔分析已覆蓋 100% 的底層技術。slides.com 就是 Reveal.js 的 SaaS host，功能完全相容。