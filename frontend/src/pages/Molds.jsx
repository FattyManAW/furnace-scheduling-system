import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { clsx } from "clsx";
import {
  Warehouse, AlertTriangle, TrendingUp, Package,
  Plus, Edit3, Minus, RotateCcw, Search, X,
} from "lucide-react";

function MoldCard({ mold, onEdit, onAdjust }) {
  const low = mold.stock_qty < 10;
  const pct = Math.min((mold.stock_qty / 50) * 100, 100);
  return (
    <div className="fade-slide-up d2 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-4 hover:border-furnace-blue/30 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-furnace-text">#{mold.mold_no}</h3>
          <p className="text-xs text-furnace-muted mt-0.5">
            OD {mold.outer_dia} × ID {mold.inner_dia} × L {mold.length}
          </p>
        </div>
        {low && (
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-furnace-red/10 text-furnace-red text-[10px] font-semibold">
            <AlertTriangle className="w-3 h-3" /> 低庫存
          </span>
        )}
      </div>
      {/* Stock bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-furnace-muted">存量</span>
          <span className={clsx("text-sm font-bold", low ? "text-furnace-red" : "text-furnace-green")}>{mold.stock_qty}</span>
        </div>
        <div className="w-full h-2 bg-furnace-border rounded-full overflow-hidden">
          <div className={clsx("h-full rounded-full transition-all", low ? "bg-furnace-red" : "bg-furnace-green")} style={{ width: `${pct}%` }} />
        </div>
      </div>
      {/* Actions */}
      <div className="flex gap-1">
        <button onClick={() => onAdjust(mold.id, 1)} className="flex-1 py-1.5 rounded-lg bg-furnace-green/10 text-furnace-green text-xs font-semibold hover:bg-furnace-green/20 flex items-center justify-center gap-1">
          <Plus className="w-3 h-3" /> 入庫
        </button>
        <button onClick={() => onAdjust(mold.id, -1)} className="flex-1 py-1.5 rounded-lg bg-furnace-amber/10 text-furnace-amber text-xs font-semibold hover:bg-furnace-amber/20 flex items-center justify-center gap-1">
          <Minus className="w-3 h-3" /> 出庫
        </button>
        <button onClick={() => onEdit(mold)} className="py-1.5 px-3 rounded-lg border border-furnace-border text-furnace-muted hover:text-furnace-blue text-xs">
          <Edit3 className="w-3 h-3" />
        </button>
      </div>
      {mold.location && <p className="text-[10px] text-furnace-muted mt-2">📍 {mold.location}</p>}
    </div>
  );
}

export default function Molds() {
  const [molds, setMolds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [lowOnly, setLowOnly] = useState(false);
  const [error, setError] = useState(null);
  const [adjusting, setAdjusting] = useState(null);
  const [adjustVal, setAdjustVal] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editMold, setEditMold] = useState(null);
  const [form, setForm] = useState({});
  const [created, setCreated] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMolds({ low_stock: lowOnly });
      setMolds(data);
      setCreated(false);
    } catch (e) { console.error(e); setError(e.message || "載入失敗"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [lowOnly]);

  const handleAdjust = async (id, delta) => {
    try {
      await api.adjustStock(id, delta, "manual");
      load();
    } catch (e) { alert(e.message); }
  };

  const openCreate = () => {
    setEditMold(null);
    setForm({ mold_no: "", outer_dia: "", inner_dia: "", length: "", stock_qty: 0, location: "", notes: "" });
    setModalOpen(true);
  };

  const openEdit = (m) => {
    setEditMold(m.id);
    setForm({ mold_no: m.mold_no, outer_dia: m.outer_dia, inner_dia: m.inner_dia, length: m.length, stock_qty: m.stock_qty, location: m.location || "", notes: m.notes || "" });
    setModalOpen(true);
  };

  const handleSave = async () => {
    const payload = {
      mold_no: form.mold_no,
      outer_dia: parseFloat(form.outer_dia) || 0,
      inner_dia: parseFloat(form.inner_dia) || 0,
      length: parseFloat(form.length) || 0,
      stock_qty: parseInt(form.stock_qty) || 0,
      location: form.location,
      notes: form.notes,
    };
    try {
      if (editMold) {
        await api.updateMold(editMold, payload);
      } else {
        await api.createMold(payload);
      }
      setModalOpen(false);
      load();
    } catch (e) { alert(e.message); }
  };

  const filtered = molds.filter(m =>
    !search || m.mold_no.includes(search) || (m.location || "").includes(search)
  );

  const lowCount = molds.filter(m => m.stock_qty < 10).length;
  const totalStock = molds.reduce((s, m) => s + m.stock_qty, 0);

  return (
    <div className="fade-slide-up d1 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">模具庫存</h1>
          <p className="text-furnace-muted text-sm mt-0.5">模具規格與存量管理</p>
        </div>
        <button onClick={openCreate} className="px-4 py-2 rounded-lg text-sm bg-furnace-green text-white flex items-center gap-1.5 hover:bg-furnace-green/90">
          <Plus className="w-4 h-4" /> 新增模具
        </button>
      </div>

      {/* Stats */}
      <div className="fade-slide-up d2 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="fade-slide-up d3 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-4">
          <p className="text-furnace-muted text-xs mb-1">模具型號</p>
          <p className="text-xl font-bold text-furnace-blue">{molds.length} 種</p>
        </div>
        <div className="fade-slide-up d4 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-4">
          <p className="text-furnace-muted text-xs mb-1">總存量</p>
          <p className="text-xl font-bold text-furnace-green">{totalStock} 支</p>
        </div>
        <div className="fade-slide-up d5 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-4">
          <p className="text-furnace-muted text-xs mb-1">低庫存警示</p>
          <p className={`text-xl font-bold ${lowCount > 0 ? "text-furnace-red" : "text-furnace-muted"}`}>{lowCount} 種</p>
        </div>
      </div>

      {/* Filters */}
      <div className="fade-slide-up d6 flex gap-3 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-furnace-muted" />
          <input type="text" placeholder="搜尋模具編號或位置..." value={search} onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-furnace-bg border border-furnace-border rounded-lg text-sm text-furnace-text" />
        </div>
        <button onClick={() => setLowOnly(!lowOnly)}
          className={clsx("px-4 py-2 rounded-lg text-sm border transition-colors", lowOnly ? "bg-furnace-red/10 border-furnace-red/30 text-furnace-red" : "border-furnace-border text-furnace-muted hover:text-furnace-text")}>
          僅低庫存
        </button>
      </div>

      {/* Grid */}
      {error ? <div className="text-center py-8"><span className="text-furnace-red bg-furnace-red/5 px-3 py-2 rounded-lg text-sm">{error}</span><button className="ml-3 text-furnace-blue text-sm underline" onClick={load}>重試</button></div> : loading ? <div className="text-furnace-muted">載入中...</div> : (
        <div className="fade-slide-up d2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map(m => <MoldCard key={m.id} mold={m} onEdit={openEdit} onAdjust={handleAdjust} />)}
        </div>
      )}

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setModalOpen(false)}>
          <div className="fade-slide-up d6 bg-furnace-card hover-lift border border-furnace-border rounded-2xl p-6 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-5">{editMold ? "編輯模具" : "新增模具"}</h2>
            <div className="fade-slide-up d2 grid grid-cols-2 gap-4">
              {[
                ["模具編號", "mold_no", "text"],
                ["外徑 OD", "outer_dia", "number"],
                ["內徑 ID", "inner_dia", "number"],
                ["長度 L", "length", "number"],
                ["初始存量", "stock_qty", "number"],
                ["位置", "location", "text"],
              ].map(([l, k, t]) => (
                <div key={k}>
                  <label className="block text-xs text-furnace-muted mb-1">{l}</label>
                  <input type={t} value={form[k] || ""} onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
                    className="w-full px-3 py-2 bg-furnace-bg border border-furnace-border rounded-lg text-sm text-furnace-text" />
                </div>
              ))}
              <div className="col-span-2">
                <label className="block text-xs text-furnace-muted mb-1">備註</label>
                <textarea value={form.notes || ""} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
                  className="w-full px-3 py-2 bg-furnace-bg border border-furnace-border rounded-lg text-sm text-furnace-text h-16 resize-none" />
              </div>
            </div>
            <div className="flex gap-3 mt-5">
              <button onClick={handleSave} className="flex-1 py-2.5 bg-furnace-green text-white rounded-lg font-semibold text-sm hover:bg-furnace-green/90">儲存</button>
              <button onClick={() => setModalOpen(false)} className="flex-1 py-2.5 border border-furnace-border rounded-lg text-sm text-furnace-muted">取消</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

