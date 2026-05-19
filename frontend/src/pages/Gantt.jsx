import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { format, addDays, startOfDay, differenceInDays, parseISO } from "date-fns";
import { zhTW } from "date-fns/locale";
import { clsx } from "clsx";
import { ChevronLeft, ChevronRight, Calendar, Info } from "lucide-react";

// ── View mode: 1週 / 2週 / 1月 ──────────────────────────────
const VIEW_MODES = [
  { label: "1週", days: 7, colW: 80 },
  { label: "2週", days: 14, colW: 80 },
  { label: "1月", days: 30, colW: 48 },
];

function timeToLeft(dateStr, minDate) {
  const d = parseISO(dateStr);
  const diff = differenceInDays(d, minDate);
  return diff * 48; // 48px per day
}

// ── 工具：以工時估算條塊跨度天數（最少 1 天）
function daysFromHours(hours) {
  return Math.max(1, Math.ceil(hours / 8));
}

// ── 按爐次利用率決定條塊顏色
function utilizationColor(pct) {
  if (pct >= 90) return "bg-furnace-red/70";
  if (pct >= 70) return "bg-furnace-orange/70";
  if (pct >= 40) return "bg-furnace-purple/70";
  return "bg-furnace-blue/70";
}

// ── Hover Tooltip
function Tooltip({ children, content }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative inline-block"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}>
      {children}
      {show && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2
          bg-furnace-card border border-furnace-border rounded-lg shadow-lg
          text-xs text-furnace-text whitespace-nowrap">
          {content}
        </div>
      )}
    </div>
  );
}

export default function Gantt() {
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewStart, setViewStart] = useState(startOfDay(new Date()));
  const [viewMode, setViewMode] = useState(0); // index into VIEW_MODES

  const days = VIEW_MODES[viewMode].days;
  const colW = VIEW_MODES[viewMode].colW;

  useEffect(() => {
    api.getScheduleResult()
      .then(setSchedule)
      .catch(() => setSchedule(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-furnace-muted">載入排程資料中...</div>;
  if (!schedule || !schedule.schedule?.length) {
    return <div className="text-furnace-muted">尚無排程結果，請先在「排程設定」頁面執行排程。</div>;
  }

  const minDate = viewStart;
  const maxDate = addDays(viewStart, days);

  // Group entries by kiln
  const kilnMap = {};
  schedule.schedule.forEach(e => {
    const kid = e.kiln_id || "unknown";
    if (!kilnMap[kid]) kilnMap[kid] = { name: "", entries: [] };
    kilnMap[kid].name = "爐 #" + kid;
    kilnMap[kid].entries.push(e);
  });

  // Use kiln_summary for names
  (schedule.kiln_summary || []).forEach(k => {
    if (kilnMap[k.kiln_id]) kilnMap[k.kiln_id].name = k.kiln_name;
  });

  const kilnIds = Object.keys(kilnMap).sort((a, b) => {
    const numA = parseInt(a) || 0;
    const numB = parseInt(b) || 0;
    return numA - numB;
  });

  // Generate date headers
  const dates = [];
  for (let i = 0; i < days; i++) {
    dates.push(addDays(minDate, i));
  }

  // ── 顏色按爐次利用率分組（非合約號）
  const kilnUsage = {};
  (schedule.kiln_summary || []).forEach(k => {
    kilnUsage[k.kiln_id] = k.usage_pct || 0;
  });

  const rowH = 48; // 加高行高

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">甘特圖</h1>
          <p className="text-furnace-muted text-sm mt-0.5">爐次排程視覺化 — 按日期與爐次分組</p>
        </div>
        <div className="flex gap-2 items-center">
          <div className="flex gap-1 bg-furnace-card border border-furnace-border rounded-lg p-1">
            {VIEW_MODES.map((m, i) => (
              <button
                key={m.label}
                onClick={() => setViewMode(i)}
                className={clsx(
                  "px-3 py-1 rounded text-xs font-semibold transition-all",
                  viewMode === i
                    ? "bg-furnace-blue text-white"
                    : "text-furnace-muted hover:text-furnace-text"
                )}
              >{m.label}</button>
            ))}
          </div>
          <button onClick={() => setViewStart(addDays(viewStart, -30))} className="p-2 rounded-lg border border-furnace-border hover:bg-furnace-border/50"><ChevronLeft className="w-4 h-4" /></button>
          <span className="text-sm text-furnace-text px-3 font-semibold">{format(viewStart, "yyyy/MM/dd")} — {format(addDays(viewStart, days), "yyyy/MM/dd")}</span>
          <button onClick={() => setViewStart(addDays(viewStart, 30))} className="p-2 rounded-lg border border-furnace-border hover:bg-furnace-border/50"><ChevronRight className="w-4 h-4" /></button>
        </div>
      </div>

      <div className="bg-furnace-card border border-furnace-border rounded-xl overflow-auto">
        <div className="inline-block min-w-full">
          {/* Header */}
          <div className="sticky top-0 bg-furnace-card border-b border-furnace-border z-10">
            <div className="flex">
              <div className="w-[140px] min-w-[140px] px-3 py-3 text-sm font-bold text-furnace-muted border-r border-furnace-border flex items-center">
                爐次
              </div>
              <div className="flex" style={{ width: days * colW }}>
                {dates.map(d => (
                  <div key={d.toISOString()} className={clsx("flex-shrink-0 text-center border-r border-furnace-border/30 py-3", d.getDay() === 0 || d.getDay() === 6 ? "bg-furnace-red/5" : "")}
                    style={{ width: colW }}>
                    <div className="text-sm font-bold text-furnace-text">{format(d, "MM/dd")}</div>
                    <div className="text-xs text-furnace-muted/70">{format(d, "EEE", { locale: zhTW })}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Rows */}
          {kilnIds.map(kid => {
            const kn = kilnMap[kid];
            const usage = kilnUsage[kid] || 0;
            return (
              <div key={kid} className="flex border-b border-furnace-border/30 hover:bg-furnace-bg/20">
                <div className="w-[140px] min-w-[140px] px-3 py-4 text-xs font-semibold text-furnace-text border-r border-furnace-border flex items-center gap-2">
                  <div className={clsx("w-2 h-2 rounded-full", usage >= 90 ? "bg-furnace-red" : usage >= 70 ? "bg-furnace-orange" : usage >= 40 ? "bg-furnace-purple" : "bg-furnace-blue")} />
                  {kn.name}
                </div>
                <div className="relative flex-shrink-0" style={{ width: days * colW, height: rowH }}>
                  {/* Background grid */}
                  {dates.map(d => (
                    <div key={d.toISOString()} className={clsx("absolute top-0 bottom-0 border-r border-furnace-border/15", d.getDay() === 0 || d.getDay() === 6 ? "bg-furnace-red/3" : "")}
                      style={{ left: differenceInDays(d, minDate) * colW, width: colW }} />
                  ))}
                  {/* Entries */}
                  {kn.entries.map(e => {
                    const d = parseISO(e.delivery_date);
                    if (d < minDate || d > maxDate) return null;
                    const left = timeToLeft(e.delivery_date, minDate);
                    const spanDays = daysFromHours(e.est_hours || 0);
                    const blockW = Math.max(60, spanDays * colW - 4); // 以時間跨度計算寬度
                    const blkColor = utilizationColor(usage);
                    return (
                      <Tooltip key={e.plan_no + e.id}
                        content={
                          <>
                            <strong>{e.plan_no}</strong><br />
                            合約: {e.contract_no || "-"} | {e.qty}支<br />
                            {e.voltage_kv}kV | {e.est_hours}h<br />
                            交期: {e.delivery_date}
                          </>
                        }>
                        <div
                          className={clsx("absolute top-2 h-[36px] rounded-lg px-3 flex items-center text-[12px] font-semibold text-white overflow-hidden whitespace-nowrap shadow-md", blkColor)}
                          style={{ left, width: blockW }}
                        >
                          {e.plan_no}
                        </div>
                      </Tooltip>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend — 爐次利用率 */}
      <div className="flex flex-wrap gap-4">
        {[
          { label: "≥90% 高負載", color: "bg-furnace-red" },
          { label: "70-90% 中高負載", color: "bg-furnace-orange" },
          { label: "40-70% 中負載", color: "bg-furnace-purple" },
          { label: "<40% 低負載", color: "bg-furnace-blue" },
        ].map(({ label, color }) => (
          <div key={label} className="flex items-center gap-1.5 text-xs">
            <div className={clsx("w-3 h-3 rounded", color)} />
            <span className="text-furnace-muted">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
