# 動畫模式（6 大類）

> 跨 4 來源萃取 · 含 CSS keyframe + JavaScript 實現

## A01：Fragment Fade-Up（逐項淡入）

最常見模式（>90% 模板採用）

```html
<div class="fragment-list">
  <p class="fragment fade-up" style="--i:0">第一項說明</p>
  <p class="fragment fade-up" style="--i:1">第二項說明</p>
  <p class="fragment fade-up" style="--i:2">第三項說明</p>
</div>
```

```css
.fragment { opacity: 0; transform: translateY(20px); transition: all 0.5s ease; }
.fragment.visible { opacity: 1; transform: translateY(0); }
/* stagger delay per item */
.fragment.fade-up { transition-delay: calc(var(--i, 0) * 0.15s); }
```

```javascript
// Intersection Observer auto-trigger
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add('visible');
  });
}, { threshold: 0.2 });
document.querySelectorAll('.fragment').forEach(el => observer.observe(el));
```

來源：34/34 模板使用 · 適合：逐點說明 · bullet 列表

## A02：Hero Number Counter（數字滾動）

從 0 滾動到目標值

```html
<span class="counter" data-target="97.8">0</span><span class="counter-suffix">%</span>
```

```javascript
function animateCounters() {
  document.querySelectorAll('.counter').forEach(el => {
    const target = parseFloat(el.dataset.target);
    const duration = 1500; // ms
    const start = performance.now();
    const startVal = parseFloat(el.textContent) || 0;
    
    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out quart
      const eased = 1 - Math.pow(1 - progress, 4);
      el.textContent = (startVal + (target - startVal) * eased).toFixed(target % 1 ? 1 : 0);
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  });
}
// Trigger on scroll into view
```

來源：metric-dashboard · 適用：KPI 數字 · 數據亮點

## A03：Staggered Grid Reveal（網格依序進場）

```html
<div class="stagger-grid">
  <div class="grid-item" style="--stagger: 0">排爐系統</div>
  <div class="grid-item" style="--stagger: 1">OTD 引擎</div>
  <div class="grid-item" style="--stagger: 2">簡報平台</div>
  <div class="grid-item" style="--stagger: 3">Kanban 看板</div>
</div>
```

```css
.grid-item {
  opacity: 0;
  transform: scale(0.95) translateY(10px);
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  transition-delay: calc(var(--stagger, 0) * 0.1s);
}
.grid-item.visible { opacity: 1; transform: scale(1) translateY(0); }
```

適用：產品特性 · 團隊成員 · grid 內容

## A04：Auto-Animate Transition（元素匹配轉場）

```javascript
// Reveal.js 原生
Reveal.initialize({
  autoAnimate: true,
  autoAnimateDuration: 0.8,
  autoAnimateEasing: 'ease',
  autoAnimateUnmatched: false,
});
```

```html
<!-- Slide 1 -->
<section data-auto-animate>
  <h2 data-id="title">排爐系統</h2>
  <div data-id="box" style="background: #2563EB; height: 50px;"></div>
</section>

<!-- Slide 2 — 元素匹配動畫 -->
<section data-auto-animate>
  <h2 data-id="title">排爐系統</h2>
  <div data-id="box" style="background: #10B981; height: 200px;"></div>
</section>
```

來源：Reveal.js 原生 · 適用：slide-to-slide 平滑過渡

## A05：Parallax Layers（視差層次）

```html
<section class="parallax-slide">
  <div class="parallax-bg" style="background-image: url('bg.jpg')"></div>
  <div class="parallax-content">
    <h2>前景標題</h2>
  </div>
</section>
```

```css
.parallax-slide { position: relative; overflow: hidden; min-height: 100vh; }
.parallax-bg {
  position: absolute; top: -20%; left: 0; right: 0; bottom: -20%;
  background-size: cover; background-position: center;
  transform: translateY(calc(var(--scroll) * 0.3));
}
.parallax-content { position: relative; z-index: 1; }
```

```javascript
// scroll-driven parallax
window.addEventListener('scroll', () => {
  const scrolled = window.pageYOffset;
  document.querySelectorAll('.parallax-bg').forEach(el => {
    el.style.setProperty('--scroll', scrolled + 'px');
  });
});
```

來源：5/34 模板使用 · 適用：品牌故事 · 感性簡報

## A06：Micro-Interactions（微互動）

```css
/* Pulse glow on hover */
.glow-hover {
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}
.glow-hover:hover {
  box-shadow: 0 0 20px rgba(37, 99, 235, 0.4);
  transform: translateY(-2px);
}

/* Success pulse */
.success-pulse {
  animation: pulse 2s ease-in-out;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  50% { box-shadow: 0 0 0 15px rgba(16, 185, 129, 0); }
}

/* Fade-slide-up variants */
.fade-slide-up { animation: fadeSlideUp 0.6s ease both; }
.fade-slide-up.d1 { animation-delay: 0.1s; }
.fade-slide-up.d2 { animation-delay: 0.2s; }
.fade-slide-up.d3 { animation-delay: 0.3s; }
/* ... d4-d8 */

@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
```

來源：全模板使用 · 適用：按鈕 · 卡片 · 數據標記

---

## 動畫選用指南

| 場景 | 推薦動畫 |
|------|------|
| Bullet 列表 | A01 Fragment Fade-Up |
| KPI 數字 | A02 Hero Number Counter |
| 產品特性 grid | A03 Staggered Grid Reveal |
| Slide 切換 | A04 Auto-Animate |
| 品牌故事 | A05 Parallax |
| 互動元素 | A06 Micro-Interactions |