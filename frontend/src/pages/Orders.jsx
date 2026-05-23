import { useEffect, useState, useRef, useCallback } from "react";
import { api } from "../lib/api";
import { format } from "date-fns";
import { clsx } from "clsx";
import { PageSkeleton, EmptyState } from "../components/Skeleton";
import {
  Search,
  Plus,
  Edit3,
  Trash2,
  X,
  Save,
  Upload,
  Filter,
  ClipboardList,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import ConfirmDialog from "../components/ConfirmDialog";

const PAGE_SIZE = 20;
const STATUSES = ["all", "pending", "scheduled", "completed"];

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const searchTimer = useRef(null);

  const handleSearch = useCallback((val) => {
    setSearch(val);
    clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => setDebouncedSearch(val), 300);
  }, []);
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({});
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulkText, setBulkText] = useState("");
  const [bulkMsg, setBulkMsg] = useState("");
  const [error, setError] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getOrders({
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
        status: statusFilter === "all" ? undefined : statusFilter,
        search: debouncedSearch || undefined,
      });
      const items = Array.isArray(data) ? data : (data.items || []);
      setOrders(items);
      const cnt = await api.countOrders(
        statusFilter === "all" ? undefined : statusFilter,
      );
      setTotal(cnt.count || 0);
    } catch (e) {
      setError(e.message || "載入失敗");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [page, statusFilter, debouncedSearch]);
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, statusFilter]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const openCreate = () => {
    setEditing(null);
    setForm({
      plan_no: "",
      contract_no: "",
      voltage_kv: "",
      current_a: "",
      qty: "",
      delivery_date: "",
      notes: "",
    });
    setModalOpen(true);
  };

  const openEdit = (o) => {
    setEditing(o.id);
    setForm({
      plan_no: o.plan_no,
      contract_no: o.contract_no || "",
      voltage_kv: o.voltage_kv,
      current_a: o.current_a,
      qty: o.qty,
      delivery_date: o.delivery_date || "",
      notes: o.notes || "",
      status: o.status,
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    // Validate required fields
    if (!form.plan_no?.trim()) { setError("計劃單號為必填"); setTimeout(() => setError(null), 4000); return; }
    const v = parseFloat(form.voltage_kv);
    const a = parseFloat(form.current_a);
    const q = parseInt(form.qty);
    if (!v || v <= 0) { setError("電壓必須大於 0"); setTimeout(() => setError(null), 4000); return; }
    if (isNaN(q) || q <= 0) { setError("數量必須至少為 1"); setTimeout(() => setError(null), 4000); return; }

    const payload = {
      plan_no: form.plan_no.trim(),
      contract_no: form.contract_no?.trim() || "",
      voltage_kv: v,
      current_a: a || 0,
      qty: q,
      delivery_date: form.delivery_date || "",
      notes: form.notes || "",
      status: form.status || "pending",
    };
    try {
      if (editing) {
        await api.updateOrder(editing, payload);
      } else {
        await api.createOrder(payload);
      }
      setModalOpen(false);
      load();
    } catch (e) {
      setError(e.message);
      setTimeout(() => setError(null), 4000);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    const id = deleteTarget;
    setDeleteTarget(null);
    try {
      await api.deleteOrder(id);
      load();
    } catch (e) {
      setError(e.message);
      setTimeout(() => setError(null), 4000);
    }
  };

  const handleBulkImport = async () => {
    setBulkMsg("匯入中...");
    try {
      const lines = bulkText.trim().split("\n");
      const orders = [];
      for (const line of lines) {
        try {
          orders.push(JSON.parse(line));
        } catch {
          continue;
        }
      }
      if (orders.length === 0) {
        setBulkMsg("❌ 無有效 JSON 資料");
        return;
      }
      const res = await api.bulkImportOrders(orders);
      setBulkMsg(`✅ 匯入 ${res.imported} 筆，跳過 ${res.skipped} 筆`);
      setBulkText("");
      load();
    } catch (e) {
      setBulkMsg(`❌ ${e.message}`);
    }
  };

  const statusBadge = (s) => {
    const map = {
      pending: "bg-furnace-amber/15 text-furnace-amber",
      scheduled: "bg-furnace-blue/15 text-furnace-blue",
      completed: "bg-furnace-green/15 text-furnace-green",
    };
    const label = { pending: "待排", scheduled: "已排", completed: "完成" };
    return (
      <span
        className={clsx(
          "px-2 py-0.5 rounded-full text-xs font-semibold",
          map[s] || "",
        )}
      >
        {label[s] || s}
      </span>
    );
  };

  return (
    <div className="fade-slide-up d1 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">訂單管理</h1>
          <p className="text-furnace-muted text-sm mt-0.5">
            管理生產訂單 — 新增、編輯、刪除、批量匯入
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setBulkOpen(!bulkOpen)}
            className="fade-slide-up d2 px-4 py-2 rounded-lg text-sm flex items-center gap-1.5 border border-furnace-border bg-furnace-card hover-lift"
          >
            <Upload className="w-4 h-4" /> 批量匯入
          </button>
          <button
            onClick={openCreate}
            className="px-4 py-2 rounded-lg text-sm bg-furnace-green text-white flex items-center gap-1.5 hover:bg-furnace-green/90"
          >
            <Plus className="w-4 h-4" /> 新增訂單
          </button>
        </div>
      </div>

      {/* Bulk Import */}
      {bulkOpen && (
        <div className="fade-slide-up d3 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">批量匯入（每行一個 JSON）</h3>
            <button onClick={() => setBulkOpen(false)}>
              <X className="w-4 h-4 text-furnace-muted" />
            </button>
          </div>
          <textarea
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
            placeholder='{"plan_no":"25-001","contract_no":"BHxxx","voltage_kv":126,"current_a":2000,"qty":3,"delivery_date":"2025-09-30"}'
            className="w-full h-32 bg-furnace-bg border border-furnace-border rounded-lg p-3 text-sm text-furnace-text font-mono resize-none"
          />
          <div className="flex items-center justify-between mt-3">
            <p className="text-xs text-furnace-muted">
              {bulkMsg || "每行一個 JSON 物件"}
            </p>
            <button
              onClick={handleBulkImport}
              className="px-4 py-2 bg-furnace-blue text-white rounded-lg text-sm hover:bg-furnace-blue/80"
            >
              執行匯入
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="fade-slide-up d4 flex gap-3 items-center bg-furnace-card hover-lift border border-furnace-border rounded-xl p-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-furnace-muted" />
          <label htmlFor="order-search" className="sr-only">搜尋計劃單號 / 合約號</label>
          <input
            id="order-search"
            type="text"
            placeholder="搜尋計劃單號 / 合約號..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-furnace-bg border border-furnace-border rounded-lg text-sm text-furnace-text placeholder:text-furnace-muted focus-visible:ring-2 focus-visible:ring-furnace-blue/40 focus-visible:outline-none"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-furnace-muted" />
          <label htmlFor="order-status-filter" className="sr-only">篩選狀態</label>
          <select
            id="order-status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-furnace-bg border border-furnace-border rounded-lg px-3 py-2 text-sm text-furnace-text focus-visible:ring-2 focus-visible:ring-furnace-blue/40 focus-visible:outline-none"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s === "all"
                  ? "全部狀態"
                  : s === "pending"
                    ? "待排"
                    : s === "scheduled"
                      ? "已排"
                      : "完成"}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="fade-slide-up d5 bg-furnace-card hover-lift border border-furnace-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-furnace-border">
                {[
                  "#",
                  "計劃單號",
                  "合約號",
                  "電壓",
                  "電流",
                  "數量",
                  "交期",
                  "狀態",
                  "操作",
                ].map((h) => (
                  <th
                    key={h}
                    className="text-left px-4 py-3 text-furnace-muted text-xs font-semibold uppercase"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {error ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center">
                    <span className="text-furnace-red bg-furnace-red/5 px-3 py-2 rounded-lg text-sm">
                      {error}
                    </span>
                    <button
                      className="ml-3 text-furnace-blue text-sm underline"
                      onClick={load}
                    >
                      重試
                    </button>
                  </td>
                </tr>
              ) : loading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8">
                    <PageSkeleton variant="table" />
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8">
                    <EmptyState
                      icon={ClipboardList}
                      label="尚無訂單資料"
                      hint="點擊「新增訂單」建立第一筆訂單"
                      actionLabel="新增訂單"
                      onAction={openCreate}
                    />
                  </td>
                </tr>
              ) : (
                orders.map((o) => (
                  <tr
                    key={o.id}
                    className="border-b border-furnace-border/50 hover:bg-furnace-bg/50"
                  >
                    <td className="px-4 py-3 text-furnace-muted text-xs">
                      {o.id}
                    </td>
                    <td className="px-4 py-3 font-semibold text-furnace-text">
                      {o.plan_no}
                    </td>
                    <td className="px-4 py-3 text-furnace-muted">
                      {o.contract_no || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-full bg-furnace-blue/10 text-furnace-blue text-xs font-semibold">
                        {o.voltage_kv} kV
                      </span>
                    </td>
                    <td className="px-4 py-3 text-furnace-muted">
                      {o.current_a} A
                    </td>
                    <td className="px-4 py-3 text-furnace-text">{o.qty} 支</td>
                    <td className="px-4 py-3 text-furnace-muted">
                      {o.delivery_date || "—"}
                    </td>
                    <td className="px-4 py-3">{statusBadge(o.status)}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        <button
                          onClick={() => openEdit(o)}
                          className="p-1.5 rounded hover:bg-furnace-border/50 text-furnace-muted hover:text-furnace-blue"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(o.id)}
                          className="p-1.5 rounded hover:bg-furnace-border/50 text-furnace-muted hover:text-furnace-red"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-furnace-border">
          <span className="text-xs text-furnace-muted">共 {total} 筆</span>
          <div className="flex gap-1">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="p-1.5 rounded hover:bg-furnace-border/50 disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              let p;
              if (totalPages <= 7) p = i + 1;
              else if (page <= 4) p = i + 1;
              else if (page >= totalPages - 3) p = totalPages - 6 + i;
              else p = page - 3 + i;
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={clsx(
                    "w-7 h-7 rounded text-xs font-semibold",
                    p === page
                      ? "bg-furnace-green text-white"
                      : "hover:bg-furnace-border/50 text-furnace-muted",
                  )}
                >
                  {p}
                </button>
              );
            })}
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="p-1.5 rounded hover:bg-furnace-border/50 disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Modal */}
      {modalOpen && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 modal-backdrop"
          onClick={() => setModalOpen(false)}
        >
          <div
            className="modal-panel bg-furnace-card hover-lift border border-furnace-border rounded-2xl p-6 w-full max-w-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold">
                {editing ? "編輯訂單" : "新增訂單"}
              </h2>
              <button
                onClick={() => setModalOpen(false)}
                className="text-furnace-muted hover:text-furnace-text"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="fade-slide-up d2 grid grid-cols-2 gap-4">
              {[
                ["計劃單號", "plan_no", "text"],
                ["合約號", "contract_no", "text"],
                ["電壓 (kV)", "voltage_kv", "number"],
                ["電流 (A)", "current_a", "number"],
                ["數量", "qty", "number"],
                ["交期", "delivery_date", "date"],
              ].map(([label, key, type]) => (
                <div key={key}>
                  <label htmlFor={`order-form-${key}`} className="block text-xs text-furnace-muted mb-1">
                    {label}
                  </label>
                  <input
                    id={`order-form-${key}`}
                    type={type}
                    value={form[key] || ""}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, [key]: e.target.value }))
                    }
                    className="w-full px-3 py-2 bg-furnace-bg border border-furnace-border rounded-lg text-sm text-furnace-text focus-visible:ring-2 focus-visible:ring-furnace-blue/40 focus-visible:outline-none"
                  />
                </div>
              ))}
              <div className="col-span-2">
                <label htmlFor="order-form-notes" className="block text-xs text-furnace-muted mb-1">
                  備註
                </label>
                <textarea
                  id="order-form-notes"
                  value={form.notes || ""}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, notes: e.target.value }))
                  }
                  className="w-full px-3 py-2 bg-furnace-bg border border-furnace-border rounded-lg text-sm text-furnace-text h-20 resize-none"
                />
              </div>
              {editing && (
                <div className="col-span-2">
                  <label htmlFor="order-form-status" className="block text-xs text-furnace-muted mb-1">
                    狀態
                  </label>
                  <select
                    id="order-form-status"
                    value={form.status || "pending"}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, status: e.target.value }))
                    }
                    className="w-full px-3 py-2 bg-furnace-bg border border-furnace-border rounded-lg text-sm text-furnace-text"
                  >
                    <option value="pending">待排</option>
                    <option value="scheduled">已排</option>
                    <option value="completed">完成</option>
                  </select>
                </div>
              )}
            </div>
            <div className="flex gap-3 mt-5">
              <button
                onClick={handleSave}
                className="flex-1 py-2.5 bg-furnace-green text-white rounded-lg font-semibold text-sm hover:bg-furnace-green/90 flex items-center justify-center gap-1.5"
              >
                <Save className="w-4 h-4" /> 儲存
              </button>
              <button
                onClick={() => setModalOpen(false)}
                className="flex-1 py-2.5 border border-furnace-border rounded-lg text-sm text-furnace-muted hover:text-furnace-text"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
      <ConfirmDialog
        open={!!deleteTarget}
        title="確定刪除？"
        message="此操作無法復原。刪除後需重新匯入資料。"
        confirmLabel="刪除"
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
