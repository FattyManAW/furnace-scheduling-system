import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { format } from "date-fns";
import {
  AlertTriangle, ClipboardList, Clock, Factory,
  Package, TrendingUp, AlertCircle, CheckCircle,
  Warehouse, Zap,
} from "lucide-react";

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="bg-furnace-card border border-furnace-border rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-furnace-muted text-xs mb-1">{label}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
          {sub && <p className="text-furnace-muted text-xs mt-1">{sub}</p>}
        </div>
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color.replace("text-furnace-", "bg-furnace-")}/15`}>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.getDashboard()
      .then(setData)
      .catch(e => setErr(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center gap-3 text-furnace-muted"><div className="spinner w-6 h-6 border-2 border-furnace-border border-t-furnace-blue rounded-full animate-spin" />載入中...</div>;
  if (err) return <div className="text-furnace-red">載入失敗: {err}</div>;
  if (!data) return null;

  const o = data.orders;
  const s = data.schedule;
  const overdueList = data.overdue_orders || [];

  const hourPct = s.daily_cap > 0 ? Math.min(s.total_hours / s.daily_cap * 100, 100) : 0;

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-furnace-text">儀表板</h1>
        <p className="text-furnace-muted text-sm mt-1">系統概況與即時資訊</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={ClipboardList} label="總訂單數" value={o.total} sub={`待排 ${o.pending} 筆`} color="text-furnace-blue" />
        <StatCard icon={Factory} label="使用爐次" value={data.kilns.active_today} sub={`共 ${data.kilns.total} 個干燥罐`} color="text-furnace-purple" />
        <StatCard icon={Clock} label="已排工時" value={`${s.total_hours.toFixed(0)}h`} sub={`剩餘 ${s.hours_remaining.toFixed(0)}h / 每日上限 ${s.daily_cap}h`} color="text-furnace-green" />
        <StatCard icon={Warehouse} label="模具型號" value={data.molds.total} sub="種規格" color="text-furnace-cyan" />
      </div>

      {/* Hour Usage Bar */}
      <div className="bg-furnace-card border border-furnace-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-furnace-text">工時使用率</h2>
          <span className={`text-sm font-bold ${hourPct > 95 ? "text-furnace-red" : hourPct > 80 ? "text-furnace-orange" : "text-furnace-green"}`}>
            {hourPct.toFixed(1)}%
          </span>
        </div>
        <div className="w-full h-3 bg-furnace-border rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${hourPct > 95 ? "bg-furnace-red" : hourPct > 80 ? "bg-furnace-orange" : "bg-furnace-green"}`}
            style={{ width: `${hourPct}%` }}
          />
        </div>
        <div className="flex justify-between mt-2 text-xs text-furnace-muted">
          <span>0h</span>
          <span>已用 {s.total_hours.toFixed(0)}h</span>
          <span>上限 {s.daily_cap}h</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Order Status */}
        <div className="bg-furnace-card border border-furnace-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-furnace-text mb-4">訂單狀態</h2>
          <div className="space-y-3">
            {[
              { label: "待排程", count: o.pending, color: "bg-furnace-orange" },
              { label: "已排入爐", count: o.scheduled, color: "bg-furnace-blue" },
              { label: "已完成", count: o.completed, color: "bg-furnace-green" },
              { label: "已逾期", count: o.overdue, color: "bg-furnace-red" },
            ].map(({ label, count, color }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-sm text-furnace-muted">{label}</span>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${color}`} />
                  <span className="text-sm font-semibold text-furnace-text">{count}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-furnace-border">
            <h3 className="text-xs font-semibold text-furnace-muted mb-2 uppercase">依合約分類（待排）</h3>
            <div className="space-y-1.5 max-h-[200px] overflow-y-auto">
              {o.pending_by_contract?.length > 0 ? o.pending_by_contract.map(c => (
                <div key={c.contract} className="flex items-center justify-between text-sm">
                  <span className="text-furnace-muted truncate mr-2">{c.contract}</span>
                  <span className="text-furnace-text">{c.count} 筆</span>
                </div>
              )) : <p className="text-furnace-muted text-sm">無</p>}
            </div>
          </div>
        </div>

        {/* Overdue Alert */}
        <div className="bg-furnace-card border border-furnace-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-furnace-text mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-furnace-orange" />
            逾期警示
          </h2>
          {overdueList.length === 0 ? (
            <div className="flex items-center gap-2 text-furnace-green py-4">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm">目前無逾期訂單</span>
            </div>
          ) : (
            <div className="space-y-2 max-h-[340px] overflow-y-auto">
              {overdueList.slice(0, 20).map(o => (
                <div key={o.id} className="flex items-center justify-between p-2.5 bg-furnace-red/5 border border-furnace-red/20 rounded-lg">
                  <div>
                    <p className="text-sm font-semibold text-furnace-text">{o.plan_no}</p>
                    <p className="text-xs text-furnace-muted">{o.contract_no} · {o.qty} 支</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-furnace-red font-semibold">
                      交期 {o.delivery_date}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

