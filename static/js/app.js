/**
 * oven_scheduler/static/js/app.js
 * Frontend logic for the Best-Fit Furnace Scheduling System.
 */

const state = {
  summary: null,
  products: {},
  orders: [],
  dryers: [],
  molds: [],
  processSteps: [],
  selectedOrderIds: new Set(),
  selectedFurnaces: new Set(),
  scheduleResult: null,
  charts: {},
};

// ─── Init ────────────────────────────────────────────────
async function init() {
  document.getElementById("clock").textContent = new Date().toLocaleString("zh-TW");
  try {
    const [summaryRes, productsRes, ordersRes, dryersRes, moldsRes, stepsRes] = await Promise.all([
      fetch("/api/summary"), fetch("/api/products"),
      fetch("/api/orders"), fetch("/api/dryers"),
      fetch("/api/molds"), fetch("/api/process-steps"),
    ]);
    state.summary = await summaryRes.json();
    state.products = await productsRes.json();
    state.orders = await ordersRes.json();
    state.dryers = await dryersRes.json();
    state.molds = await moldsRes.json();
    state.processSteps = await stepsRes.json();

    document.getElementById("data-loaded").textContent = `✅ ${state.orders.length} 筆訂單 · ${state.dryers.length} 罐 · ${Object.keys(state.products).length} 產品`;
    renderDashboard();
    renderOrders();
    renderFurnaceSelect();
    renderFurnacesPage();
    renderMoldsPage();
  } catch(e) {
    toast("資料載入失敗: " + e.message, "error");
  }
}

// ─── Navigation ─────────────────────────────────────────
function showPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll("nav button").forEach(b => b.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  document.querySelector(`nav button[onclick*="${id}"]`)?.classList.add("active");
}

// ─── Dashboard ──────────────────────────────────────────
function renderDashboard() {
  const { orders, dryers, molds, products } = state;

  // Stats
  const deliverDates = [...new Set(orders.map(o => o.delivery_date))];
  const productKVs = [...new Set(orders.map(o => o.voltage_kv))];
  const totalMolds = molds.reduce((s, m) => s + m.qty, 0);

  document.getElementById("dashboard-stats").innerHTML = `
    <div class="stat-card">
      <span class="label">總訂單數</span>
      <span class="value" style="color:var(--accent)">${orders.length}</span>
      <span class="sub">支</span>
    </div>
    <div class="stat-card">
      <span class="label">產品種類</span>
      <span class="value" style="color:var(--info)">${Object.keys(products).length}</span>
      <span class="sub">種規格</span>
    </div>
    <div class="stat-card">
      <span class="label">乾燥罐</span>
      <span class="value" style="color:var(--warn)">${dryers.length}</span>
      <span class="sub">台</span>
    </div>
    <div class="stat-card">
      <span class="label">模具庫存</span>
      <span class="value" style="color:var(--success)">${molds.length}</span>
      <span class="sub">種規格 · ${totalMolds} 根</span>
    </div>
    <div class="stat-card">
      <span class="label">交期範圍</span>
      <span class="value" style="font-size:1.3rem; color:var(--text2)">${deliverDates[0] || '-'}</span>
      <span class="sub">至 ${deliverDates[deliverDates.length-1] || '-'}</span>
    </div>
  `;

  // Voltage distribution chart
  const kvCount = {};
  orders.forEach(o => { kvCount[o.voltage_kv] = (kvCount[o.voltage_kv] || 0) + o.qty; });
  const sortedKVs = Object.entries(kvCount).sort((a,b) => parseFloat(a[0]) - parseFloat(b[0]));
  const colors = sortedKVs.map((_, i) => `hsl(${220 + i * 12}, 75%, 65%)`);

  renderChart("chart-voltage", "doughnut", {
    labels: sortedKVs.map(([kv]) => `${kv}kV`),
    datasets: [{
      data: sortedKVs.map(([,cnt]) => cnt),
      backgroundColor: colors,
      borderWidth: 0,
    }],
  }, { plugins: { legend: { position: "right", labels: { color: "#e2e4ed", font: { size: 11 } } } } });

  // Delivery date bar chart (top 20 dates)
  const dateCount = {};
  orders.forEach(o => { dateCount[o.delivery_date] = (dateCount[o.delivery_date] || 0) + o.qty; });
  const sortedDates = Object.entries(dateCount).sort().slice(0, 20);

  renderChart("chart-dates", "bar", {
    labels: sortedDates.map(([d]) => d.slice(5)),
    datasets: [{
      label: "訂單數量",
      data: sortedDates.map(([,cnt]) => cnt),
      backgroundColor: "rgba(108,124,255,.6)",
      borderRadius: 4,
    }],
  }, { plugins: { legend: { display: false } }, scales: {
    x: { ticks: { color: "#8b8fa8", font: { size: 10 }, maxRotation: 45 },
        grid: { color: "rgba(46,49,80,.3)" } },
    y: { ticks: { color: "#8b8fa8" }, grid: { color: "rgba(46,49,80,.3)" } },
  }});

  // Mold stock table
  const moldBody = document.querySelector("#mold-stock-table tbody");
  moldBody.innerHTML = molds.map(m => `<tr><td>${m.od}</td><td>${m.id_inner}</td><td>${m.length}</td><td><span class="badge badge-success">${m.qty} 根</span></td></tr>`).join("");

  // Dryer summary table
  const dryBody = document.querySelector("#dryer-summary-table tbody");
  dryBody.innerHTML = dryers.map(d => `<tr><td>${d.name}</td><td>${d.inner_d}mm</td><td>${d.height}mm</td><td><span class="badge badge-accent">${d.plans} 方案</span></td></tr>`).join("");
}

// ─── Orders Page ─────────────────────────────────────────
function renderOrders() {
  const kvOptions = {};
  state.orders.forEach(o => kvOptions[o.voltage_kv] = true);
  const kvSelect = document.getElementById("filter-kv");
  kvSelect.innerHTML = '<option value="">全部</option>' +
    Object.keys(kvOptions).sort((a,b) => a-b).map(kv => `<option value="${kv}">${kv} kV</option>`).join("");

  filterOrders();
}

function filterOrders() {
  const search = document.getElementById("order-search").value.toLowerCase();
  const kv = document.getElementById("filter-kv").value;
  const start = document.getElementById("filter-start").value;
  const end = document.getElementById("filter-end").value;

  const filtered = state.orders.filter(o => {
    if (search && !o.order_id.toLowerCase().includes(search) && !o.contract.toLowerCase().includes(search))
      return false;
    if (kv && o.voltage_kv != kv) return false;
    if (start && o.delivery_date < start) return false;
    if (end && o.delivery_date > end) return false;
    return true;
  });

  document.getElementById("order-count").textContent = filtered.length;
  const wrap = document.getElementById("orders-list");

  if (filtered.length === 0) {
    wrap.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--text2)">沒有符合條件的訂單</div>`;
    return;
  }

  wrap.innerHTML = `
    <div class="order-row header">
      <div><input type="checkbox" id="chk-all" onchange="toggleAllOrders(this)"></div>
      <div>訂單號</div><div>合約</div><div>電壓</div><div>電流</div><div>數量</div><div>交期</div><div>模具規格</div>
    </div>
    ${filtered.map(o => {
      const kv = o.voltage_kv;
      const amp = o.current_a;
      const spec = state.products[`${kv}/${amp}`];
      const specStr = spec ? `${spec.mold_od}×${spec.mold_id}×${spec.mold_length}mm` : "—";
      const checked = state.selectedOrderIds.has(o.order_id) ? "checked" : "";
      return `
        <div class="order-row">
          <div><input type="checkbox" class="order-chk" value="${o.order_id}" ${checked} onchange="toggleOrder('${o.order_id}', this.checked)"></div>
          <div><strong>${o.order_id}</strong></div>
          <div style="color:var(--text2)">${o.contract}</div>
          <div><span class="badge badge-accent">${kv} kV</span></div>
          <div>${amp} A</div>
          <div>${o.qty} <span style="color:var(--text2);font-size:0.8rem">支</span></div>
          <div>${o.delivery_date}</div>
          <div style="font-size:0.8rem;color:var(--text2)">${specStr}</div>
        </div>
      `;
    }).join("")}
  `;
}

function toggleOrder(id, checked) {
  if (checked) state.selectedOrderIds.add(id); else state.selectedOrderIds.delete(id);
}

function toggleAllOrders(el) {
  const chks = document.querySelectorAll(".order-chk");
  chks.forEach(c => { c.checked = el.checked; if(el.checked) state.selectedOrderIds.add(c.value); else state.selectedOrderIds.delete(c.value); });
}

function selectAllOrders() {
  state.orders.forEach(o => state.selectedOrderIds.add(o.order_id));
  filterOrders();
}

function clearAllOrders() {
  state.selectedOrderIds.clear();
  filterOrders();
}

function goToScheduleWithSelected() {
  showPage("page-schedule");
}

// ─── Schedule Page ───────────────────────────────────────
function renderFurnaceSelect() {
  const wrap = document.getElementById("furnace-chips");
  wrap.innerHTML = state.dryers.map(d =>
    `<span class="chip ${state.selectedFurnaces.has(d.name) ? 'active' : ''}" onclick="toggleFurnace('${d.name}', this)">${d.name}</span>`
  ).join("");
}

function toggleFurnace(name, el) {
  if (state.selectedFurnaces.has(name)) {
    state.selectedFurnaces.delete(name);
    el.classList.remove("active");
  } else {
    state.selectedFurnaces.add(name);
    el.classList.add("active");
  }
}

async function runOptimize() {
  const source = document.querySelector("input[name=order-source"]:checked")?.value || "selected";
  let orderIds = [];
  let orders;

  if (source === "selected") {
    orderIds = [...state.selectedOrderIds];
    orders = state.orders.filter(o => orderIds.includes(o.order_id));
    if (orderIds.length === 0) { toast("請先在訂單管理頁面選擇訂單", "warn"); return; }
  } else if (source === "all") {
    orders = state.orders;
  } else if (source === "date") {
    const start = document.getElementById("schedule-date-start").value;
    const end = document.getElementById("schedule-date-end").value;
    if (!start || !end) { toast("請設定交期範圍", "warn"); return; }
    orders = state.orders.filter(o => o.delivery_date >= start && o.delivery_date <= end);
  }

  const btn = document.getElementById("btn-optimize");
  document.getElementById("opt-label").innerHTML = '<span class="spinner"></span> 計算中…';
  btn.disabled = true;

  try {
    const res = await fetch("/api/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_ids: orderIds, furnaces: source === "selected" || source === "date" ? null : [...state.selectedFurnaces] }),
    });
    const result = await res.json();
    state.scheduleResult = result;
    renderScheduleResult(result);
    document.getElementById("results-area").style.display = "block";
    document.getElementById("no-result-msg").style.display = "none";
    toast(`排爐完成！${result.total_batches} 批次，${result.furnace_count} 個乾燥罐`, "success");
  } catch(e) {
    toast("排爐失敗: " + e.message, "error");
  } finally {
    document.getElementById("opt-label").textContent = "▶ 執行最佳化排爐";
    btn.disabled = false;
  }
}

function renderScheduleResult(r) {
  // Stats
  const totalMolds = r.batches.reduce((s,b) => s + b.total_molds, 0);
  const avgUtil = r.batches.length > 0 ? Math.round(totalMolds / (r.furnace_count * Math.max(1, r.total_days)) * 100) : 0;
  document.getElementById("result-stats").innerHTML = `
    <div class="stat-card"><span class="label">總批次數</span><span class="value" style="color:var(--accent)">${r.total_batches}</span></div>
    <div class="stat-card"><span class="label">使用乾燥罐</span><span class="value" style="color:var(--info)">${r.furnace_count}</span></div>
    <div class="stat-card"><span class="label">總模具數</span><span class="value" style="color:var(--warn)">${totalMolds}</span></div>
    <div class="stat-card"><span class="label">排程總天數</span><span class="value" style="color:var(--success)">${r.total_days || 0}</span></div>
  `;

  // Utilization per furnace
  const fUtil = {};
  r.batches.forEach(b => { fUtil[b.furnace] = (fUtil[b.furnace] || 0) + b.total_molds; });
  const maxDay = Math.max(...Object.values(r.furnace_day), 1);

  destroyChart("chart-utilization");
  renderChart("chart-utilization", "bar", {
    labels: Object.keys(fUtil),
    datasets: [{
      label: "入罐模具總數",
      data: Object.values(fUtil),
      backgroundColor: "rgba(0,210,160,.5)",
      borderColor: "rgba(0,210,160,.8)",
      borderWidth: 1,
      borderRadius: 4,
    }],
  }, { plugins: { legend: { display: false } }, scales: {
    x: { ticks: { color: "#8b8fa8", font: { size: 10 }, maxRotation: 45 }, grid: { color: "rgba(46,49,80,.3)" } },
    y: { ticks: { color: "#8b8fa8" }, grid: { color: "rgba(46,49,80,.3)" }, title: { display: true, text: "模具數量", color: "#8b8fa8" } },
  }});

  // Batch sizes
  const sizeDist = {};
  r.batches.forEach(b => { const k = b.total_molds; sizeDist[k] = (sizeDist[k] || 0) + 1; });
  destroyChart("chart-batch-sizes");
  renderChart("chart-batch-sizes", "bar", {
    labels: Object.keys(sizeDist).sort((a,b) => a-b).map(k => `${k} 根/批`),
    datasets: [{
      label: "批次數",
      data: Object.keys(sizeDist).sort((a,b) => a-b).map(k => sizeDist[k]),
      backgroundColor: "rgba(108,124,255,.6)",
      borderRadius: 4,
    }],
  }, { plugins: { legend: { display: false } }, scales: {
    x: { ticks: { color: "#8b8fa8" }, grid: { color: "rgba(46,49,80,.3)" } },
    y: { ticks: { color: "#8b8fa8", stepSize: 1 }, grid: { color: "rgba(46,49,80,.3)" } },
  }});

  // Gantt
  renderGantt(r);

  // Batch table
  document.getElementById("batch-table").innerHTML = r.batches.map(b => {
    const ms = b.mold_spec || {};
    const ordersStr = b.molds.map(m => `${m.order_id}(${m.qty})`).join(", ");
    const ordersSpec = b.molds.map(m => `${m.voltage_kv}/${m.current_a}A`).join(", ");
    return `<tr>
      <td><span class="badge badge-accent">${b.batch_id}</span></td>
      <td><strong>${b.furnace}</strong></td>
      <td>方案 ${b.plan}</td>
      <td>${ms.od||'?'} × ${ms.id||'?'} × ${ms.length||'?'} mm</td>
      <td><span class="badge badge-success">${b.total_molds} 根</span></td>
      <td style="font-size:0.78rem">${ordersStr}</td>
      <td>${ordersSpec}</td>
    </tr>`;
  }).join("");
}

function renderGantt(r) {
  if (r.batches.length === 0) {
    document.getElementById("gantt-container").innerHTML = `<p style="text-align:center;color:var(--text2);padding:1rem">無批次資料</p>`;
    return;
  }

  // Build per-furnace rows
  const fRows = {};
  r.batches.forEach(b => {
    if (!fRows[b.furnace]) fRows[b.furnace] = [];
    fRows[b.furnace].push(b);
  });

  const maxDay = Math.max(r.total_days, 1);
  const dayWidth = 28;
  const totalWidth = maxDay * dayWidth + 200;

  let html = `<table class="gantt-table"><thead><tr>
    <th style="width:130px">乾燥罐</th>
    <th style="width:80px">方案</th>
    ${Array.from({length: maxDay}, (_, i) => `<th style="width:${dayWidth}px">D${i+1}</th>`).join("")}
  </tr></thead><tbody>`;

  for (const [fname, batches] of Object.entries(fRows)) {
    // Row per batch
    batches.forEach((b, idx) => {
      const ms = b.mold_spec || {};
      const left = b.start_day * dayWidth + 200;
      const width = Math.max(1, b.total_molds) * dayWidth + 40;
      const colorIdx = b.total_molds % 5;
      const colors = ["#6c7cff","#00d2a0","#ffb347","#47b3ff","#ff5c7c","#c084fc","#fb923c","#34d399"];
      const bg = colors[colorIdx % colors.length];
      html += `<tr>
        <td class="furnace-name">${idx === 0 ? `<strong>${fname}</strong><br><span style="font-size:0.7rem;color:var(--text2)">${b.furnace_spec}</span>` : ""}</td>
        <td style="font-size:0.75rem">方案${b.plan}</td>
        ${Array.from({length: maxDay}, (_, d) => `<td></td>`).join("")}
      </tr>`;
      // Note: the bar is in next pseudo-row — instead render inline
    });

    // Simpler: one row with inline block bars
  }

  // Rebuild: one gantt row per furnace with colored blocks
  html = `<table class="gantt-table"><thead><tr>
    <th style="width:150px">乾燥罐</th>
    <th style="width:60px">方案</th>
    ${Array.from({length: maxDay}, (_, i) => `<th style="width:${dayWidth}px">D${i+1}</th>`).join("")}
  </tr></thead><tbody>`;

  for (const [fname, batches] of Object.entries(fRows)) {
    const first = batches[0];
    html += `<tr>
      <td class="furnace-name" style="vertical-align:middle">
        <strong>${fname}</strong><br>
        <span style="font-size:0.7rem;color:var(--text2)">${first.furnace_spec}</span>
      </td>
      <td style="font-size:0.75rem;color:var(--text2);vertical-align:middle">
        ${[...new Set(batches.map(b=>b.plan))].join(",")}
      </td>
    `;
    // Draw blocks via position:relative cell
    html += `<td colspan="${maxDay}" style="position:relative;height:48px;padding:0;vertical-align:middle">`;
    batches.forEach(b => {
      const ms = b.mold_spec || {};
      const pct = (b.start_day / maxDay) * 100;
      const durPct = Math.max(8, (1 / maxDay) * 100 * Math.max(1, b.total_molds * 0.3));
      const colors = ["#6c7cff","#00d2a0","#ffb347","#47b3ff","#ff5c7c","#c084fc","#fb923c","#34d399"];
      const bg = colors[b.batch_id.charCodeAt(2) % colors.length];
      html += `<div style="position:absolute;left:${pct}%;width:${durPct}%;height:28px;background:${bg};border-radius:6px;top:10px;
        font-size:0.68rem;color:#fff;display:flex;align-items:center;justify-content:center;overflow:hidden;white-space:nowrap;font-weight:600;padding:0 4px"
        title="${b.batch_id}: ${b.total_molds}根 (${b.molds.map(m=>m.order_id).join(',')})">
        ${b.batch_id} ${b.total_molds}根
      </div>`;
    });
    html += `</td></tr>`;
  }

  html += `</tbody></table>`;
  document.getElementById("gantt-container").innerHTML = html;
}

// ─── Furnaces Page ───────────────────────────────────────
function renderFurnacesPage() {
  const grid = document.getElementById("furnace-detail-grid");
  grid.innerHTML = state.dryers.map(d => `
    <div class="card">
      <div class="card-title" style="color:var(--accent)">${d.name}</div>
      <div style="font-size:0.85rem;color:var(--text2);margin-bottom:12px">
        內徑 Φ${d.inner_d}mm × 高度 ${d.height}mm
      </div>
      <div class="furnace-plans">
        ${d.plans.map(p => `
          <div style="flex:1;min-width:200px;background:var(--bg);border-radius:8px;padding:10px;border:1px solid var(--border)">
            <div style="font-weight:700;font-size:0.82rem;margin-bottom:8px">方案 ${p.plan}</div>
            <div style="font-size:0.78rem;color:var(--text2)">
              <div>上層: ${p.upper.qty} 根 · Φ${p.upper.od}×${p.upper.id}×${p.upper.length}mm</div>
              <div>下層: ${p.lower.qty} 根 · Φ${p.lower.od}×${p.lower.id}×${p.lower.length}mm</div>
            </div>
          </div>
        `).join("")}
      </div>
    </div>
  `).join("");
}

// ─── Molds Page ──────────────────────────────────────────
function renderMoldsPage() {
  // Mold table
  document.getElementById("mold-table").innerHTML = state.molds.map((m, i) => `
    <tr>
      <td>${i+1}</td>
      <td>${m.od}</td><td>${m.id_inner}</td><td>${m.length}</td>
      <td><span class="badge badge-success">${m.qty} 根</span></td>
    </tr>
  `).join("");

  // Coverage chart
  const moldKeys = state.molds.map(m => `${m.od}×${m.id_inner}×${m.length}`);
  const values = state.molds.map(m => m.qty);

  destroyChart("chart-mold-coverage");
  renderChart("chart-mold-coverage", "bar", {
    labels: moldKeys,
    datasets: [{
      label: "庫存數量",
      data: values,
      backgroundColor: values.map(v => v < 30 ? "rgba(255,179,71,.6)" : "rgba(0,210,160,.5)"),
      borderRadius: 3,
    }],
  }, { indexAxis: "y", plugins: { legend: { display: false } }, scales: {
    x: { ticks: { color: "#8b8fa8" }, grid: { color: "rgba(46,49,80,.3)" } },
    y: { ticks: { color: "#8b8fa8", font: { size: 10 } }, grid: { color: "rgba(46,49,80,.3)" } },
  }});
}

// ─── Export ──────────────────────────────────────────────
function exportCSV() {
  if (!state.scheduleResult) return;
  fetch("/api/export/csv", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ batches: state.scheduleResult.batches }),
  }).then(r => r.blob()).then(blob => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `排爐計劃_${new Date().toISOString().slice(0,10)}.csv`;
    a.click(); URL.revokeObjectURL(url);
    toast("CSV 已匯出", "success");
  });
}

// ─── Chart helpers ───────────────────────────────────────
function renderChart(id, type, data, opts = {}) {
  destroyChart(id);
  const ctx = document.getElementById(id)?.getContext("2d");
  if (!ctx) return;
  const defaultOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { tooltip: { backgroundColor: "#212436", titleColor: "#e2e4ed", bodyColor: "#e2e4ed", borderColor: "#2e3150", borderWidth: 1 } },
  };
  state.charts[id] = new Chart(ctx, { type, data, options: { ...defaultOpts, ...opts } });
}

function destroyChart(id) {
  if (state.charts[id]) { state.charts[id].destroy(); delete state.charts[id]; }
}

// ─── Toast ───────────────────────────────────────────────
function toast(msg, type = "info") {
  const el = document.getElementById("toast");
  const colors = { info: "#47b3ff", success: "#00d2a0", warn: "#ffb347", error: "#ff5c7c" };
  el.style.borderLeft = `4px solid ${colors[type] || colors.info}`;
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 3500);
}

// ─── Boot ────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", init);
