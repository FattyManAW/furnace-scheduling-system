/** API client wrapper — fetch + error handling */
// Backend URL — change for your deployment:
//   Docker/Tailscale: http://100.107.36.80:8002
//   Local dev:        http://localhost:8002
// Same-origin when served behind nginx; set to backend URL for dev mode
const API_BASE =
  window.location.hostname === "localhost" ? "http://localhost:8002" : "";

async function req(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...opts.headers },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  return res.json();
}

export const api = {
  // ── Orders ──
  getOrders: (params) => {
    const q = new URLSearchParams();
    if (params?.skip) q.set("skip", params.skip);
    if (params?.limit) q.set("limit", params.limit);
    if (params?.status) q.set("status", params.status);
    if (params?.search) q.set("search", params.search);
    return req(`/api/v1/orders/?${q}`);
  },
  getOrder: (id) => req(`/api/v1/orders/${id}`),
  createOrder: (data) =>
    req("/api/v1/orders/", { method: "POST", body: JSON.stringify(data) }),
  updateOrder: (id, data) =>
    req(`/api/v1/orders/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteOrder: (id) => req(`/api/v1/orders/${id}`, { method: "DELETE" }),
  countOrders: (status) => {
    const q = status ? `?status=${encodeURIComponent(status)}` : "";
    return req(`/api/v1/orders/count${q}`);
  },
  bulkImportOrders: (orders) =>
    req("/api/v1/orders/bulk-import", {
      method: "POST",
      body: JSON.stringify(orders),
    }),

  // ── Molds ──
  getMolds: (params) => {
    const q = new URLSearchParams();
    if (params?.skip) q.set("skip", params.skip);
    if (params?.limit) q.set("limit", params.limit);
    if (params?.low_stock) q.set("low_stock", "true");
    return req(`/api/v1/molds/?${q}`);
  },
  getMold: (id) => req(`/api/v1/molds/${id}`),
  createMold: (data) =>
    req("/api/v1/molds/", { method: "POST", body: JSON.stringify(data) }),
  updateMold: (id, data) =>
    req(`/api/v1/molds/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  adjustStock: (id, delta, reason) =>
    req(
      `/api/v1/molds/${id}/stock?delta=${delta}&reason=${encodeURIComponent(reason)}`,
    ),

  // ── Kilns ──
  getKilns: () => req("/api/v1/kilns/"),
  getKilnDetail: (id) => req(`/api/v1/kilns/${id}`),

  // ── Schedule ──
  runSchedule: (orderIds, strategy = "deadline") =>
    req("/api/v1/schedule/optimize", {
      method: "POST",
      body: JSON.stringify({ order_ids: orderIds, strategy }),
    }),
  getScheduleResult: () => req("/api/v1/schedule/result"),
  getKilnSchedule: (id) => req(`/api/v1/schedule/${id}/schedule`),

  // ── Reports ──
  getDashboard: () => req("/api/v1/reports/dashboard"),
  exportOrdersCsv: (status) => {
    const q = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetch(`${API_BASE}/api/v1/reports/orders/csv${q}`);
  },
  exportScheduleCsv: () => fetch(`${API_BASE}/api/v1/reports/schedule/csv`),
  exportOrdersJson: () => req("/api/v1/reports/orders/json"),

  // ── Kanban ──
  getKanban: () => req("/api/v1/kanban"),
  updateKanbanItem: (id, status) =>
    req(`/api/v1/kanban/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
};
