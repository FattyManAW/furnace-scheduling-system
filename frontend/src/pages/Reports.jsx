import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { clsx } from "clsx";
import {
  Download,
  FileText,
  FileSpreadsheet,
  Calendar as CalIcon,
} from "lucide-react";
import { PageSkeleton, EmptyState } from "../components/Skeleton";

export default function Reports() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getDashboard()
      .then(setDashboard)
      .catch((e) => {
        setError(e.message || "載入失敗");
      })
      .finally(() => setLoading(false));
  }, []);

  const downloadCsv = async (url, filename) => {
    const res = await fetch(url);
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
  };

  if (error)
    return (
      <div className="text-center py-8">
        <span className="text-furnace-red bg-furnace-red/5 px-3 py-2 rounded-lg text-sm">
          {error}
        </span>
        <button
          className="ml-3 text-furnace-blue text-sm underline"
          onClick={() => {
            setError(null);
            setLoading(true);
            api
              .getDashboard()
              .then(setDashboard)
              .catch((e) => setError(e.message || "載入失敗"))
              .finally(() => setLoading(false));
          }}
        >
          重試
        </button>
      </div>
    );
  if (loading) return <PageSkeleton variant="cards" />;
  if (!dashboard)
    return <div className="text-furnace-muted">無法載入報表資料</div>;

  const o = dashboard.orders;
  const s = dashboard.schedule;

  return (
    <div className="fade-slide-up d1 space-y-5">
      <div>
        <h1 className="text-2xl font-bold">報表匯出</h1>
        <p className="text-furnace-muted text-sm mt-0.5">報表匯出與統計資料</p>
      </div>

      {/* KPI Cards */}
      <div className="fade-slide-up d2 grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "總訂單", val: o.total, color: "text-furnace-blue" },
          { label: "待排", val: o.pending, color: "text-furnace-amber" },
          { label: "已排", val: o.scheduled, color: "text-furnace-green" },
          {
            label: "總工時",
            val: `${s.total_hours.toFixed(0)}h`,
            color: "text-furnace-purple",
          },
        ].map(({ label, val, color }) => (
          <div
            key={label}
            className="fade-slide-up d2 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-4"
          >
            <p className="text-furnace-muted text-xs">{label}</p>
            <p className={clsx("text-2xl font-bold mt-1", color)}>{val}</p>
          </div>
        ))}
      </div>

      {/* CSV Export */}
      <div className="fade-slide-up d3 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
        <h2 className="text-sm font-semibold text-furnace-text mb-4">
          CSV 匯出
        </h2>
        <div className="fade-slide-up d2 grid grid-cols-1 md:grid-cols-3 gap-3">
          <button
            onClick={() =>
              downloadCsv("/api/v1/reports/orders/csv", "orders.csv")
            }
            className="flex items-center gap-3 p-4 rounded-xl border border-furnace-border hover:border-furnace-green/30 hover:bg-furnace-green/5 transition-colors group"
          >
            <div className="w-10 h-10 rounded-lg bg-furnace-green/10 flex items-center justify-center">
              <FileSpreadsheet className="w-5 h-5 text-furnace-green" />
            </div>
            <div className="text-left">
              <p className="text-sm font-semibold text-furnace-text group-hover:text-furnace-green">
                訂單 CSV
              </p>
              <p className="text-xs text-furnace-muted">匯出所有訂單資料</p>
            </div>
            <Download className="w-4 h-4 text-furnace-muted ml-auto" />
          </button>

          <button
            onClick={() =>
              downloadCsv("/api/v1/reports/schedule/csv", "schedule.csv")
            }
            className="flex items-center gap-3 p-4 rounded-xl border border-furnace-border hover:border-furnace-blue/30 hover:bg-furnace-blue/5 transition-colors group"
          >
            <div className="w-10 h-10 rounded-lg bg-furnace-blue/10 flex items-center justify-center">
              <CalIcon className="w-5 h-5 text-furnace-blue" />
            </div>
            <div className="text-left">
              <p className="text-sm font-semibold text-furnace-text group-hover:text-furnace-blue">
                排程 CSV
              </p>
              <p className="text-xs text-furnace-muted">匯出當前排程結果</p>
            </div>
            <Download className="w-4 h-4 text-furnace-muted ml-auto" />
          </button>

          <button
            onClick={() =>
              downloadCsv("/api/v1/reports/orders/json", "orders.json")
            }
            className="flex items-center gap-3 p-4 rounded-xl border border-furnace-border hover:border-furnace-purple/30 hover:bg-furnace-purple/5 transition-colors group"
          >
            <div className="w-10 h-10 rounded-lg bg-furnace-purple/10 flex items-center justify-center">
              <FileText className="w-5 h-5 text-furnace-purple" />
            </div>
            <div className="text-left">
              <p className="text-sm font-semibold text-furnace-text group-hover:text-furnace-purple">
                訂單 JSON
              </p>
              <p className="text-xs text-furnace-muted">匯出完整 JSON 格式</p>
            </div>
            <Download className="w-4 h-4 text-furnace-muted ml-auto" />
          </button>
        </div>
      </div>

      {/* Pending by Contract */}
      <div className="fade-slide-up d4 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
        <h2 className="text-sm font-semibold text-furnace-text mb-4">
          待排訂單 — 依合約分類
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-furnace-border">
                {["合約號", "訂單數", "總數量"].map((h) => (
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
              {o.pending_by_contract?.map((c) => (
                <tr
                  key={c.contract}
                  className="border-b border-furnace-border/30"
                >
                  <td className="px-4 py-3 font-semibold">{c.contract}</td>
                  <td className="px-4 py-3 text-furnace-muted">{c.count} 筆</td>
                  <td className="px-4 py-3 text-furnace-text">{c.qty} 支</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Overdue */}
      {dashboard.overdue_orders?.length > 0 && (
        <div className="bg-furnace-red/5 border border-furnace-red/20 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-furnace-red mb-3">
            逾期訂單
          </h2>
          <div className="fade-slide-up d2 grid grid-cols-1 md:grid-cols-2 gap-2">
            {dashboard.overdue_orders.map((o) => (
              <div
                key={o.id}
                className="fade-slide-up d5 flex items-center justify-between p-3 bg-furnace-card hover-lift rounded-lg border border-furnace-border"
              >
                <span className="text-sm font-semibold">{o.plan_no}</span>
                <div className="text-right">
                  <p className="text-xs text-furnace-red">{o.contract_no}</p>
                  <p className="text-xs text-furnace-muted">
                    交期: {o.delivery_date}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
