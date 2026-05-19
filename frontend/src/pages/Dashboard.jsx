import { useEffect, useState } from "react";
import { api } from "../lib/api";
import {
  AlertTriangle, ClipboardList, Clock, Factory,
  CheckCircle, Warehouse, TrendingUp,
} from "lucide-react";

/* ── Skeleton Placeholder ── */
function Skeleton({ className = "" }) {
  return <div className={`skeleton animate-pulse ${className}`} />;
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="載入中">
      <div>
        <Skeleton className="h-8 w-36 mb-2" />
        <Skeleton className="h-4 w-56" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-furnace-card border border-furnace-border rounded-xl p-5">
            <Skeleton className="h-3 w-20 mb-3" />
            <Skeleton className="h-7 w-16 mb-2" />
            <Skeleton className="h-3 w-24" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
      <span className="sr-only">儀表板資料載入中...</span>
    </div>
  );
}

/* ── KPI Card (ISA-101 grey + semantic accents) ── */
function KpiCard({ icon: Icon, label, value, sub, accent }) {
  const accentBg = {
    blue:   "bg-furnace-blue/10",
    green:  "bg-furnace-green/10",
    amber:  "bg-furnace-amber/10",
    purple: "bg-furnace-purple/10",
    cyan:   "bg-furnace-cyan/10",
    red:    "bg-furnace-red/10",
  };
  const accentText = {
    blue:   "text-furnace-blue",
    green:  "text-furnace-green",
    amber:  "text-furnace-amber",
    purple: "text-furnace-purple",
    cyan:   "text-furnace-cyan",
    red:    "text-furnace-red",
  };

  return (
    <div className="bg-furnace-card border border-furnace-border hover:border-furnace-hover rounded-xl p-5 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-furnace-muted text-xs uppercase tracking-wider mb-2">{label}</p>
          <p className={`text-[28px] font-bold leading-tight ${accentText[accent] || "text-furnace-heading"}`}>
            {value}
          </p>
          {sub && (
            <p className="text-furnace-muted text-xs mt-1.5">{sub}</p>
          )}
        </div>
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center ml-3 flex-shrink-0 ${accentBg[accent] || "bg-furnace-hover"}`}>
          <Icon className={`w-5 h-5 ${accentText[accent] || "text-furnace-muted"}`} />
        </div>
      </div>
    </div>
  );
}

/* ── Progress bar ── */
function ProgressBar({ pct, label, used, cap }) {
  const barColor = pct > 95 ? "bg-furnace-red" : pct > 80 ? "bg-furnace-amber" : "bg-furnace-green";
  const textColor = pct > 95 ? "text-furnace-red" : pct > 80 ? "text-furnace-amber" : "text-furnace-green";

  return (
    <div className="bg-furnace-card border border-furnace-border rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-furnace-heading">{label}</h2>
        <span className={`text-sm font-bold ${textColor}`}>{pct.toFixed(1)}%</span>
      </div>
      <div className="w-full h-2.5 bg-furnace-border rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <div className="flex justify-between mt-2 text-xs text-furnace-muted">
        <span>0h</span>
        <span>已用 {used}h</span>
        <span>上限 {cap}h</span>
      </div>
    </div>
  );
}

/* ── Status row ── */
function StatusRow({ label, count, color, total }) {
  const pct = total > 0 ? (count / total * 100).toFixed(0) : 0;
  return (
    <div className="flex items-center justify-between py-2.5">
      <div className="flex items-center gap-3">
        <span className={`w-2.5 h-2.5 rounded-full bg-furnace-${color}`} />
        <span className="text-sm text-furnace-text">{label}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-furnace-muted">{pct}%</span>
        <span className="text-sm font-semibold text-furnace-heading tabular-nums min-w-[2rem] text-right">{count}</span>
      </div>
    </div>
  );
}

/* ─── Main Dashboard ─── */
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

  if (loading) return <DashboardSkeleton />;
  if (err) return (
    <div className="bg-furnace-red/10 border border-furnace-red/20 text-furnace-red rounded-xl p-5 text-sm">
      <AlertTriangle className="inline w-4 h-4 mr-2" />
      載入失敗：{err}
      <button className="ml-3 underline hover:text-furnace-heading" onClick={() => { setLoading(true); setErr(null); api.getDashboard().then(setData).catch(e => setErr(e.message)).finally(() => setLoading(false)); }}>
        重試
      </button>
    </div>
  );
  if (!data) return null;

  const o = data.orders;
  const s = data.schedule;
  const overdueList = data.overdue_orders || [];
  const hourPct = s.daily_cap > 0 ? Math.min(s.total_hours / s.daily_cap * 100, 100) : 0;

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-furnace-heading">儀表板</h1>
        <p className="text-furnace-muted text-sm mt-1 flex items-center gap-2">
          <TrendingUp className="w-4 h-4" />
          系統概況與即時統計
        </p>
      </div>

      {/* ── KPI Four-Card (Bento Grid) ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard icon={ClipboardList} label="總訂單數" value={o.total} sub={`待排 ${o.pending} 筆`} accent="blue" />
        <KpiCard icon={Factory} label="運作中乾燥罐" value={`${data.kilns.active_today}/${data.kilns.total}`} sub="今日排程" accent="purple" />
        <KpiCard icon={Clock} label="預估總工時" value={`${s.total_hours.toFixed(0)}h`} sub={`每日上限 ${s.daily_cap}h`} accent={hourPct > 80 ? "amber" : "green"} />
        <KpiCard icon={Warehouse} label="模具型號庫" value={data.molds.total} sub="種規格" accent="cyan" />
      </div>

      {/* ── Hour Usage Bar ── */}
      <ProgressBar pct={hourPct} label="工時使用率" used={s.total_hours.toFixed(0)} cap={s.daily_cap} />

      {/* ── Orders / Overdue two-col ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Order Status Breakdown */}
        <div className="bg-furnace-card border border-furnace-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-furnace-heading mb-4">訂單狀態分佈</h2>
          <div className="divide-y divide-furnace-border">
            <StatusRow label="待排程" count={o.pending} color="amber" total={o.total} />
            <StatusRow label="已排入爐" count={o.scheduled} color="blue" total={o.total} />
            <StatusRow label="已完成" count={o.completed} color="green" total={o.total} />
            <StatusRow label="已逾期" count={o.overdue} color="red" total={o.total} />
          </div>
          {o.pending_by_contract?.length > 0 && (
            <div className="mt-4 pt-4 border-t border-furnace-border">
              <h3 className="text-xs font-semibold text-furnace-muted mb-2 uppercase tracking-wider">合約別（待排）</h3>
              <div className="space-y-1 max-h-[160px] overflow-y-auto">
                {o.pending_by_contract.map(c => (
                  <div key={c.contract} className="flex items-center justify-between text-sm py-1">
                    <span className="text-furnace-muted truncate mr-2">{c.contract}</span>
                    <span className="text-furnace-text font-medium">{c.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Overdue Alert */}
        <div className="bg-furnace-card border border-furnace-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-furnace-heading mb-4 flex items-center gap-2">
            {overdueList.length > 0 ? (
              <AlertTriangle className="w-4 h-4 text-furnace-red" />
            ) : (
              <CheckCircle className="w-4 h-4 text-furnace-green" />
            )}
            逾期警示
            {overdueList.length > 0 && (
              <span className="text-furnace-red text-xs ml-2">（{overdueList.length} 筆）</span>
            )}
          </h2>
          {overdueList.length === 0 ? (
            <p className="text-furnace-muted text-sm py-4">目前無逾期訂單</p>
          ) : (
            <div className="space-y-2 max-h-[370px] overflow-y-auto pr-1">
              {overdueList.slice(0, 30).map(o => (
                <div key={o.id} className="p-3 bg-furnace-red/5 border border-furnace-red/10 rounded-lg hover:border-furnace-red/25 transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-furnace-heading">{o.plan_no}</p>
                      <p className="text-xs text-furnace-muted mt-0.5">{o.contract_no || "—"} · {o.qty} 支</p>
                    </div>
                    <p className="text-xs font-semibold text-furnace-red bg-furnace-red/10 px-2 py-1 rounded-md tabular-nums">
                      交期 {o.delivery_date}
                    </p>
                  </div>
                </div>
              ))}
              {overdueList.length > 30 && (
                <p className="text-xs text-furnace-muted text-center pt-1">...還有 {overdueList.length - 30} 筆</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}