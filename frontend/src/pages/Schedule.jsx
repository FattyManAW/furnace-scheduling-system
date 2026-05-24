import { useEffect, useState } from "react";
import { api } from "../lib/api";
import usePageTitle from "../lib/usePageTitle";
import { clsx } from "clsx";
import { PageSkeleton, EmptyState } from "../components/Skeleton";
import { useToast } from "../components/Toast";
import {
  Play,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  ChevronDown,
} from "lucide-react";

const STRATEGIES = [
  { value: "deadline", label: "交期優先", desc: "優先排入最早交期的訂單" },
  { value: "fill", label: "填滿優先", desc: "優先填滿同一爐的槽位" },
  { value: "balance", label: "平衡模式", desc: "平衡各爐使用量" },
];

export default function Schedule() {
  usePageTitle("排程設定");
  const toast = useToast();
  const [kilns, setKilns] = useState([]);
  const [orders, setOrders] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [strategy, setStrategy] = useState("deadline");
  const [recentRuns, setRecentRuns] = useState([]);
  const [expandedKiln, setExpandedKiln] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getKilns(), api.getOrders({ limit: 500 })])
      .then(([ks, os]) => {
        setKilns(Array.isArray(ks) ? ks : (ks.items || []));
        setOrders(Array.isArray(os) ? os : (os.items || []));
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, []);

  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === orders.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(orders.map((o) => o.id)));
    }
  };

  const handleRun = async () => {
    setRunning(true);
    setErr(null);
    setResult(null);
    try {
      const ids = selected.size > 0 ? [...selected] : undefined;
      const data = await api.runSchedule(ids, strategy);
      setResult(data);
      toast.success(`排程完成！已排入 ${data.summary.scheduled} 筆訂單`);
      setRecentRuns((prev) =>
        [
          {
            time: new Date().toLocaleString("zh-TW"),
            strategy,
            scheduled: data.summary.scheduled,
            hours: data.summary.total_hours,
            skipped: data.summary.skipped,
          },
          ...prev,
        ].slice(0, 5),
      );
      // Refresh kilns to show schedule
      const ks = await api.getKilns();
      setKilns(Array.isArray(ks) ? ks : (ks.items || []));
    } catch (e) {
      setErr(e.message);
      toast.error(`排程失敗：${e.message}`);
    } finally {
      setRunning(false);
    }
  };

  const sortedOrders = [...orders].sort((a, b) =>
    (a.delivery_date || "").localeCompare(b.delivery_date || ""),
  );

  return (
    <div className="fade-slide-up d1 space-y-5">
      <div>
        <h1 className="text-2xl font-bold">排程設定</h1>
        <p className="text-furnace-muted text-sm mt-0.5">
          設定排程策略與執行優化
        </p>
      </div>

      {loading ? (
        <PageSkeleton variant="table" />
      ) : err && orders.length === 0 ? (
        <div className="text-center py-8">
          <span className="text-furnace-red bg-furnace-red/5 px-3 py-2 rounded-lg text-sm">
            ⚠️ {err}
          </span>
        </div>
      ) : (
        <>
          {/* Strategy Selection */}
          <div className="fade-slide-up d2 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-furnace-text mb-4">
              排程策略
            </h2>
            <div className="fade-slide-up d2 grid grid-cols-1 md:grid-cols-3 gap-3">
              {STRATEGIES.map((s) => (
                <button
                  key={s.value}
                  onClick={() => setStrategy(s.value)}
                  aria-pressed={strategy === s.value}
                  aria-label={`排程策略：${s.label}`}
                  className={clsx(
                    "p-4 rounded-xl border-2 text-left transition-all",
                    strategy === s.value
                      ? "border-furnace-green bg-furnace-green/5"
                      : "border-furnace-border hover:border-furnace-muted",
                  )}
                >
                  <p
                    className={clsx(
                      "font-semibold text-sm",
                      strategy === s.value
                        ? "text-furnace-green"
                        : "text-furnace-text",
                    )}
                  >
                    {s.label}
                  </p>
                  <p className="text-xs text-furnace-muted mt-1">{s.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Execute */}
          <div className="fade-slide-up d3 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-furnace-text">
                選擇訂單
              </h2>
              <span className="text-xs text-furnace-muted">
                已選 {selected.size} / {orders.length} 筆
              </span>
            </div>

            {/* Quick selection */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={toggleAll}
                className="text-xs px-3 py-1.5 rounded-full border border-furnace-border text-furnace-muted hover:text-furnace-text"
              >
                {selected.size === orders.length ? "取消全選" : "全選"}
              </button>
              <button
                onClick={() =>
                  setSelected(
                    new Set(
                      orders
                        .filter((o) => o.status === "pending")
                        .map((o) => o.id),
                    ),
                  )
                }
                className="text-xs px-3 py-1.5 rounded-full border border-furnace-border text-furnace-muted hover:text-furnace-text"
              >
                只選待排
              </button>
            </div>

            {/* Order list (scrollable) */}
            <div className="max-h-[300px] overflow-y-auto border border-furnace-border rounded-lg">
              <table className="w-full text-xs">
                <caption className="sr-only">待排程訂單列表</caption>
                <thead className="fade-slide-up d4 sticky top-0 bg-furnace-card hover-lift">
                  <tr className="border-b border-furnace-border">
                    <th className="px-3 py-2 w-10">
                      <label htmlFor="schedule-select-all" className="sr-only">全選</label>
                      <input
                        id="schedule-select-all"
                        type="checkbox"
                        checked={
                          selected.size === orders.length && orders.length > 0
                        }
                        onChange={toggleAll}
                      />
                    </th>
                    {["計劃單號", "合約號", "電壓", "數量", "交期"].map((h) => (
                      <th
                        key={h}
                        scope="col"
                        className="text-left px-3 py-2 text-furnace-muted font-semibold"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedOrders.map((o) => (
                    <tr
                      key={o.id}
                      className="border-b border-furnace-border/30 hover:bg-furnace-bg/30"
                    >
                      <td className="px-3 py-2">
                        <label htmlFor={`schedule-select-${o.id}`} className="sr-only">選擇 {o.plan_no}</label>
                        <input
                          id={`schedule-select-${o.id}`}
                          type="checkbox"
                          checked={selected.has(o.id)}
                          onChange={() => toggleSelect(o.id)}
                        />
                      </td>
                      <td className="px-3 py-2 font-semibold">{o.plan_no}</td>
                      <td className="px-3 py-2 text-furnace-muted">
                        {o.contract_no || "—"}
                      </td>
                      <td className="px-3 py-2 text-furnace-muted">
                        {o.voltage_kv} kV
                      </td>
                      <td className="px-3 py-2 text-furnace-muted">
                        {o.qty} 支
                      </td>
                      <td className="px-3 py-2 text-furnace-muted">
                        {o.delivery_date || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {err && <p className="text-furnace-red text-sm mt-3">⚠️ {err}</p>}

            <button
              onClick={handleRun}
              disabled={running || orders.length === 0}
              aria-label={running ? "排程計算中" : "開始排程優化"}
              className={clsx(
                "mt-4 px-6 py-3 rounded-xl font-bold text-sm flex items-center gap-2 transition-all",
                running
                  ? "bg-furnace-border text-furnace-muted cursor-wait"
                  : "bg-gradient-to-r from-furnace-green to-furnace-cyan text-white hover:opacity-90",
              )}
            >
              {running ? (
                <>
                  <div className="w-4 h-4 border-2 border-furnace-muted border-t-white rounded-full animate-spin" />{" "}
                  排程計算中...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> 開始排程
                </>
              )}
            </button>
          </div>

          {/* Result */}
          {result && (
            <div className="fade-slide-up d1 space-y-4 success-pulse rounded-xl">
              {/* Summary Cards */}
              <div className="fade-slide-up d2 grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  {
                    label: "已排入",
                    val: result.summary.scheduled,
                    color: "text-furnace-green",
                    icon: CheckCircle,
                  },
                  {
                    label: "未排入",
                    val: result.summary.skipped,
                    color: "text-furnace-red",
                    icon: AlertTriangle,
                  },
                  {
                    label: "總工時",
                    val: `${result.summary.total_hours.toFixed(0)}h`,
                    color: "text-furnace-blue",
                    icon: Clock,
                  },
                  {
                    label: "使用爐數",
                    val: result.kiln_summary.length,
                    color: "text-furnace-purple",
                    icon: Zap,
                  },
                ].map(({ label, val, color, icon: Icon }) => (
                  <div
                    key={label}
                    className="fade-slide-up d5 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-furnace-muted text-xs">{label}</p>
                        <p className={clsx("text-2xl font-bold mt-1", color)}>
                          {val}
                        </p>
                      </div>
                      <Icon className={clsx("w-5 h-5", color)} />
                    </div>
                  </div>
                ))}
              </div>

              {/* Warnings */}
              {result.warnings?.length > 0 && (
                <div className="bg-furnace-amber/5 border border-furnace-amber/20 rounded-xl p-4">
                  <p className="text-furnace-amber font-semibold text-sm mb-2">
                    ⚠️ 排程警示 ({result.warnings.length})
                  </p>
                  <div className="fade-slide-up d1 space-y-1 max-h-40 overflow-y-auto">
                    {result.warnings.map((w) => (
                    <p key={w} className="text-xs text-furnace-muted">
                        {w}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Kiln Results */}
              <div className="fade-slide-up d6 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
                <h2 className="text-sm font-semibold text-furnace-text mb-4">
                  爐況排程結果
                </h2>
                <div className="fade-slide-up d1 space-y-2">
                  {result.kiln_summary.map((k) => {
                    const isExpanded = expandedKiln === k.kiln_id;
                    const pct = k.usage_pct;
                    const barColor =
                      pct > 95
                        ? "bg-furnace-red"
                        : pct > 80
                          ? "bg-furnace-amber"
                          : "bg-furnace-green";
                    return (
                      <div
                        key={k.kiln_id}
                        className="border border-furnace-border rounded-xl overflow-hidden"
                      >
                        <button
                          onClick={() =>
                            setExpandedKiln(isExpanded ? null : k.kiln_id)
                          }
                          className="w-full px-4 py-3 flex items-center justify-between hover:bg-furnace-bg/50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <span className="font-semibold text-sm text-furnace-text">
                              {k.kiln_name}
                            </span>
                            <span className="text-xs text-furnace-muted">
                              {k.slots_used}/{k.total_slots} 槽位 ·{" "}
                              {k.order_count} 筆
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="w-32 h-2 bg-furnace-border rounded-full overflow-hidden">
                              <div
                                className={clsx(
                                  "h-full rounded-full",
                                  barColor,
                                )}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span
                              className={clsx(
                                "text-xs font-bold",
                                pct > 95
                                  ? "text-furnace-red"
                                  : pct > 80
                                    ? "text-furnace-amber"
                                    : "text-furnace-green",
                              )}
                            >
                              {pct}%
                            </span>
                            <ChevronDown
                              className={clsx(
                                "w-4 h-4 text-furnace-muted transition-transform",
                                isExpanded && "rotate-180",
                              )}
                            />
                          </div>
                        </button>
                        {isExpanded && (
                          <div className="px-4 pb-3 border-t border-furnace-border/50">
                            <table className="w-full text-xs mt-2">
                              <caption className="sr-only">排程結果詳情</caption>
                              <thead>
                                <tr className="text-furnace-muted">
                                  <th scope="col" className="text-left py-1.5">計劃單號</th>
                                  <th scope="col" className="text-left py-1.5">數量</th>
                                  <th scope="col" className="text-right py-1.5">工時</th>
                                </tr>
                              </thead>
                              <tbody>
                                {k.orders.map((o) => (
                                  <tr
                                    key={o.plan_no || o.order_id}
                                    className="border-t border-furnace-border/30"
                                  >
                                    <td className="py-1.5 font-semibold">
                                      {o.plan_no}
                                    </td>
                                    <td className="py-1.5 text-furnace-muted">
                                      {o.qty} 支
                                    </td>
                                    <td className="py-1.5 text-right text-furnace-muted">
                                      {o.hours}h
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Recent Runs */}
          {recentRuns.length > 0 && (
            <div className="fade-slide-up d6 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
              <h2 className="text-sm font-semibold text-furnace-muted mb-3">
                最近排程記錄
              </h2>
              <div className="fade-slide-up d1 space-y-2">
                {recentRuns.map((r) => (
                  <div
                    key={r.time + r.strategy}
                    className="flex items-center justify-between text-xs py-1.5 border-b border-furnace-border/30 last:border-0"
                  >
                    <span className="text-furnace-muted">{r.time}</span>
                    <span className="text-furnace-text">
                      {STRATEGIES.find((s) => s.value === r.strategy)?.label}
                    </span>
                    <span className="text-furnace-green">
                      {r.scheduled} 已排
                    </span>
                    <span className="text-furnace-red">{r.skipped} 跳過</span>
                    <span className="text-furnace-muted">
                      {r.hours.toFixed(0)}h
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
