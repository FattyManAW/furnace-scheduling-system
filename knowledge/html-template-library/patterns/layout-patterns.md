# 版面佈局模式（10 種）

> 跨 4 來源萃取 · 含 HTML 骨架 + CSS 規則

## L01：Hero with Stats（封面 + 數字）

```html
<section class="hero-slide">
  <div class="hero-content">
    <h1 class="hero-title">標題</h1>
    <p class="hero-subtitle">副標題 · 日期 · 作者</p>
    <div class="hero-stats">
      <div class="stat"><span class="stat-number">91</span><span class="stat-label">功能完成</span></div>
      <div class="stat"><span class="stat-number">100%</span><span class="stat-label">OTD 達成</span></div>
      <div class="stat"><span class="stat-number">7</span><span class="stat-label">服務上線</span></div>
    </div>
  </div>
</section>
```

```css
.hero-slide {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; padding: 4rem;
  background: var(--c-bg);
}
.hero-title { font: 700 3.5rem/1.2 var(--f-display); color: var(--c-primary); }
.hero-subtitle { font: 300 1.25rem var(--f-body); color: var(--c-text-muted); margin-top: 1rem; }
.hero-stats { display: flex; gap: 3rem; margin-top: 3rem; }
.stat-number { font: 700 3rem var(--f-display); color: var(--c-accent); display: block; }
.stat-label { font: 400 0.875rem var(--f-body); color: var(--c-text-muted); }
```

來源：34/34 模板使用 · 適合：封面 · KPI slide · 開場

## L02：Split Panel（左右分割）

```html
<section class="split-panel">
  <div class="split-left">
    <h2>左側標題</h2>
    <p>說明文字...</p>
  </div>
  <div class="split-right">
    <div class="image-placeholder">圖表或圖片</div>
  </div>
</section>
```

```css
.split-panel { display: grid; grid-template-columns: 1fr 1fr; min-height: 100vh; }
.split-left { padding: 4rem; display: flex; flex-direction: column; justify-content: center; }
.split-right { background: var(--c-secondary); display: flex; align-items: center; justify-content: center; }
```

來源：22/34 模板使用 · 適合：對比 · 問題/解決方案 · 前後對照

## L03：Grid Cards（網格卡片）

```html
<section class="grid-cards">
  <h2 class="section-title">區塊標題</h2>
  <div class="card-grid">
    <div class="card">
      <div class="card-icon">🔧</div>
      <h3>排爐系統</h3>
      <p>42 API · 甘特圖 · 即時排程</p>
    </div>
    <!-- repeat 3-6 cards -->
  </div>
</section>
```

```css
.card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
.card { background: var(--c-card); padding: 2rem; border: 1px solid var(--c-border); border-radius: 8px; }
.card-icon { font-size: 2rem; margin-bottom: 0.75rem; }
```

來源：30/34 模板使用 · 適合：產品特性 · 團隊介紹 · 功能一覽

## L04：Timeline（時間線）

```html
<section class="timeline">
  <h2>開發歷程</h2>
  <div class="timeline-track">
    <div class="timeline-item">
      <div class="timeline-dot"></div>
      <div class="timeline-content">
        <span class="timeline-date">05/18</span>
        <h4>Phase 0 基礎建置</h4>
        <p>排爐 v1 → FastAPI 重構</p>
      </div>
    </div>
    <!-- repeat items -->
  </div>
</section>
```

```css
.timeline-track { position: relative; padding-left: 2rem; border-left: 2px solid var(--c-border); }
.timeline-dot { position: absolute; left: -0.5rem; width: 0.75rem; height: 0.75rem; background: var(--c-accent); border-radius: 50%; }
.timeline-item { position: relative; margin-bottom: 2rem; padding-left: 1.5rem; }
```

來源：15/34 模板使用 · 適合：里程碑 · 開發歷程 · Roadmap

## L05：Comparison Table（對比表格）

```html
<section class="comparison">
  <h2>版本對比</h2>
  <table class="compare-table">
    <thead><tr><th>指標</th><th>v1.1</th><th>v2.0</th><th>Δ</th></tr></thead>
    <tbody>
      <tr class="pass"><td>OTD%</td><td>100%</td><td>100%</td><td>✅ 0pp</td></tr>
      <tr class="warn"><td>完成率</td><td>99.3%</td><td>100%</td><td>⚠️ +0.7pp</td></tr>
    </tbody>
  </table>
</section>
```

```css
.compare-table { width: 100%; border-collapse: collapse; }
.compare-table th { background: var(--c-primary); color: white; padding: 0.75rem 1rem; text-align: left; }
.compare-table td { padding: 0.75rem 1rem; border-bottom: 1px solid var(--c-border); }
.compare-table tr:nth-child(even) { background: var(--c-bg); }
.pass { border-left: 3px solid #10B981; }
.warn { border-left: 3px solid #F59E0B; }
```

來源：10/34 模板使用 · 適合：數據對比 · 版本差異 · spec 比較

## L06：Quote/Testimonial（引用/證言）

```html
<section class="testimonial">
  <blockquote>
    <p class="quote-text">"Customer success story quote..."</p>
    <cite>— Name, Role at Company</cite>
  </blockquote>
  <div class="testimonial-stats">
    <div class="stat"><span class="stat-number">+35%</span><span>效率提升</span></div>
  </div>
</section>
```

```css
.testimonial { display: flex; flex-direction: column; align-items: center; min-height: 100vh; justify-content: center; padding: 4rem; }
blockquote { max-width: 36rem; text-align: center; }
.quote-text { font: italic 300 2rem/1.5 var(--f-display); color: var(--c-primary); }
cite { font: 400 1rem var(--f-body); color: var(--c-text-muted); margin-top: 1.5rem; display: block; }
```

適合：案例營銷 · 客戶證言 · 結尾頁（含 CTA）

## L07：KPI Dashboard（數字儀表板）

```html
<section class="kpi-dashboard">
  <h2>本月關鍵指標</h2>
  <div class="kpi-grid">
    <div class="kpi-card">
      <span class="kpi-value up" data-target="100">0</span>
      <span class="kpi-label">OTD%</span>
      <span class="kpi-delta positive">↑ 5%</span>
    </div>
    <!-- repeat 4-6 KPI cards -->
  </div>
</section>
```

```css
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.kpi-card { background: var(--c-card); padding: 1.5rem; text-align: center; border: 1px solid var(--c-border); border-radius: 8px; }
.kpi-value { font: 700 3.5rem var(--f-display); display: block; }
.kpi-value.up { color: var(--c-accent-up); }
.kpi-label { font: 400 0.875rem var(--f-body); color: var(--c-text-muted); margin-top: 0.25rem; display: block; }
```

來源：metric-dashboard · data-dense（4 模板）· 適合：OKR 報告 · Dashboard

## L08：Image-First（影像主導）

```html
<section class="image-first" style="background-image: url('bg.jpg')">
  <div class="image-overlay">
    <h2>標題在圖上</h2>
    <p>副標題 · 半透明背景確保可讀性</p>
  </div>
</section>
```

```css
.image-first { background-size: cover; background-position: center; min-height: 100vh; }
.image-overlay { background: rgba(0,0,0,0.5); min-height: 100vh; padding: 4rem; display: flex; flex-direction: column; justify-content: center; color: white; }
```

來源：rule-of-thirds · velvet-night（5 模板）· 適合：感性簡報 · 品牌故事

## L09：Code/Spec（技術規格）

```html
<section class="code-spec">
  <h2>API 規格</h2>
  <pre class="code-block"><code>GET /api/v1/schedule
→ { "orders": [...], "otd": 0.98 }</code></pre>
  <div class="spec-table">
    <div class="spec-row"><span>Endpoint</span><span>/health</span></div>
    <div class="spec-row"><span>Method</span><span>GET</span></div>
  </div>
</section>
```

```css
.code-block { background: var(--c-secondary); padding: 1.5rem; border-radius: 8px; font: 400 1rem var(--f-mono); }
.spec-table { margin-top: 1.5rem; }
.spec-row { display: flex; padding: 0.5rem 0; border-bottom: 1px solid var(--c-border); }
.spec-row span:first-child { font-weight: 600; min-width: 8rem; }
```

適合：API 文件 · 技術簡報 · 開發者導向

## L10：Closing CTA（結尾行動呼籲）

```html
<section class="closing-cta">
  <h2>感謝聆聽</h2>
  <p class="cta-text">立即聯繫我們，開始優化您的工廠排程</p>
  <div class="cta-buttons">
    <a href="#" class="btn-primary">預約 Demo</a>
    <a href="#" class="btn-secondary">下載白皮書</a>
  </div>
  <div class="contact-info">
    <span>📧 henry@cris-ai.com</span>
    <span>🌐 cris-ai.com</span>
  </div>
</section>
```

```css
.closing-cta { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; text-align: center; padding: 4rem; }
.cta-text { font: 300 1.5rem var(--f-body); color: var(--c-text-muted); margin: 1.5rem 0; max-width: 30rem; }
.cta-buttons { display: flex; gap: 1rem; margin-top: 2rem; }
.btn-primary { background: var(--c-primary); color: white; padding: 0.75rem 2rem; border-radius: 6px; text-decoration: none; font-weight: 600; }
.btn-secondary { border: 2px solid var(--c-primary); color: var(--c-primary); padding: 0.75rem 2rem; border-radius: 6px; text-decoration: none; font-weight: 600; }
```

適合：結尾頁 · 所有簡報的最終 slide