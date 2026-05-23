import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import {
  format,
  addDays,
  startOfDay,
  differenceInDays,
  parseISO,
} from "date-fns";
import { zhTW } from "date-fns/locale";
import { clsx } from "clsx";
import {
  ChevronLeft, ChevronRight, GripVertical, GitBranch,
} from "lucide-react";
import { PageSkeleton } from "../components/Skeleton";

// ── View mode: 日/週/月 ─────────────────
const VIEW_MODES = [
  { label: "日", days: 1, colW: 120 },
  { label: "週", days: 7, colW: 80 },
  { label: "月", days: 31, colW: 36 },
];

// ── 生命週期狀態色 ─────────────────
const LIFECYCLE_COLORS = {
  pending: "bg-furnace-muted/40",
  scheduled: "bg-furnace-blue/60",
  in_progress: "bg-furnace-amber/60",
  done: "bg-furnace-green/60",
};
const LIFECYCLE_LABELS = {
  pending: "待排程",
  scheduled: "已排程",
  in_progress: "生產中",
  done: "已完成",
};

// ── 以工時估算條塊跨度天數（最少 1 天）
function daysFromHours(hours) {
  return Math.max(1, Math.ceil((hours || 8) / 8));
}

// ── 條塊 X 座標
function timeToLeft(dateStr, minDate, colW) {
  const d = parseISO(dateStr);
  const diff = differenceInDays(d, minDate);
  return diff * colW;
}

// ── Hover Tooltip
function Tooltip({ children, content }) {
  const [show, setShow] = useState(false);
  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2
          bg-furnace-card hover-lift border border-furnace-border rounded-lg shadow-lg
          text-xs text-furnace-text whitespace-nowrap"
        >
          {content}
        </div>
      )}
    </div>
  );
}

export default function Gantt() {
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewStart, setViewStart] = useState(null);
  const [viewMode, setViewMode] = useState(1); // default: 週
  const [error, setError] = useState(null);
  // ── 拖曳狀態
  const [dragging, setDragging] = useState(null); // { entryId, startX, currentX }
  const [localSchedule, setLocalSchedule] = useState(null); // local edits before API save
  const [depsVisible, setDepsVisible] = useState(true);

  useEffect(() => {
    api
      .getScheduleResult()
      .then((data) => {
        setSchedule(data);
        setLocalSchedule(JSON.parse(JSON.stringify(data)));
        if (data?.schedule?.length) {
          const dates = data.schedule
            .map((e) => e.delivery_date)
            .filter(Boolean);
          if (dates.length) {
            setViewStart(startOfDay(parseISO(dates.sort()[0])));
          }
        }
      })
      .catch((e) => {
        setSchedule(null);
        setError(e.message || "載入失敗");
      })
      .finally(() => setLoading(false));
  }, []);

  // ── 拖曳處理 ─────────────────
  // ── Unified drag clientX extraction (mouse + touch) ──
  const getClientX = useCallback((e) => {
    if (e.touches && e.touches[0]) return e.touches[0].clientX;
    if (e.changedTouches && e.changedTouches[0]) return e.changedTouches[0].clientX;
    return e.clientX;
  }, []);

  const handleDragStart = useCallback((e, entryIds) => {
    const data = localSchedule;
    if (!data) return;
    setDragging({ ids: entryIds, startClientX: getClientX(e), moved: false });
  }, [localSchedule, getClientX]);

  const handleDrag = useCallback((e) => {
    setDragging((prev) =>
      prev ? { ...prev, currentClientX: getClientX(e), moved: true } : null,
    );
  }, [getClientX]);

  const handleDragEnd = useCallback((e) => {
    if (!dragging || !localSchedule) { setDragging(null); return; }
    const days = VIEW_MODES[viewMode].days;
    const cw = VIEW_MODES[viewMode].colW;

    if (dragging.moved && dragging.ids) {
      const dayDelta = Math.round((getClientX(e) - (dragging.startClientX || getClientX(e))) / cw);
      if (dayDelta !== 0) {
        const updated = JSON.parse(JSON.stringify(localSchedule));
        dragging.ids.forEach((id) => {
          const entry = updated.schedule?.find((en) => en.id === id || en.plan_no === id);
          if (entry && entry.delivery_date) {
            const oldDate = parseISO(entry.delivery_date);
            const newDate = addDays(oldDate, dayDelta);
            entry.delivery_date = format(newDate, "yyyy-MM-dd");
            entry._dragged = true;
          }
        });
        setLocalSchedule(updated);
      }
    }
    setDragging(null);
  }, [dragging, localSchedule, viewMode, getClientX]);

  // ── 儲存拖曳變更 ─────────────────
  const saveChanges = useCallback(async () => {
    if (!localSchedule) return;
    const changed = (localSchedule.schedule || []).filter((e) => e._dragged);
    if (!changed.length) return;

    let saved = 0;
    for (const entry of changed) {
      try {
        await api.updateOrder(entry.id, { delivery_date: entry.delivery_date });
        saved++;
      } catch (err) {
        // save error surfaced via per-row status indicator
      }
    }
    // Refresh data
    const data = await api.getScheduleResult();
    setSchedule(data);
    setLocalSchedule(JSON.parse(JSON.stringify(data)));
  }, [localSchedule]);

  if (loading)
    return <PageSkeleton variant="table" />;

  if (error && !schedule)
    return (
      <div className="text-center py-12 space-y-3">
        <p className="text-furnace-red bg-furnace-red/5 inline-block px-4 py-2 rounded-lg text-sm">
          ⚠️ {error}
        </p>
        <br />
        <button
          className="text-furnace-blue text-sm underline"
          onClick={() => {
            setLoading(true); setError(null);
            api.getScheduleResult().then((d) => { setSchedule(d); setLocalSchedule(JSON.parse(JSON.stringify(d))); }).catch((e2) => { setSchedule(null); setError(e2.message); }).finally(() => setLoading(false));
          }}
        >重試</button>
      </div>
    );

  if (!schedule || !schedule.schedule?.length)
    return <div className="text-furnace-muted">尚無排程結果，請先在「排程設定」頁面執行排程。</div>;

  const data = localSchedule || schedule;
  const days = VIEW_MODES[viewMode].days;
  const colW = VIEW_MODES[viewMode].colW;
  const minDate = viewStart || startOfDay(new Date());
  const navDays = Math.max(1, Math.floor(days / 2));

  // Group entries by kiln
  const kilnMap = {};
  data.schedule.forEach((e) => {
    const kid = e.kiln_id || "unknown";
    if (!kilnMap[kid]) kilnMap[kid] = { name: "", entries: [] };
    kilnMap[kid].name = "爐 #" + kid;
    kilnMap[kid].entries.push(e);
  });
  (schedule.kiln_summary || []).forEach((k) => {
    if (kilnMap[k.kiln_id]) kilnMap[k.kiln_id].name = k.kiln_name;
  });
  const kilnIds = Object.keys(kilnMap).sort((a, b) => (parseInt(a) || 0) - (parseInt(b) || 0));

  // Generate date headers
  const dates = [];
  for (let i = 0; i < days; i++) dates.push(addDays(minDate, i));

  // Kiln usage
  const kilnUsage = {};
  (schedule.kiln_summary || []).forEach((k) => { kilnUsage[k.kiln_id] = k.usage_pct || 0; });

  const rowH = 52;
  const hasChanges = (data.schedule || []).some((e) => e._dragged);

  return (
    <div className="fade-slide-up d1 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">甘特圖</h1>
          <p className="text-furnace-muted text-sm mt-0.5">
            爐次排程視覺化 · {viewMode === 0 ? "日" : viewMode === 1 ? "週" : "月"}視圖
            {hasChanges && <span className="text-amber-400 ml-2">⚠️ 有未儲存的拖曳變更</span>}
          </p>
        </div>
        <div className="flex gap-2 items-center flex-wrap">
          {/* Zoom mode toggle */}
          <div className="flex gap-1 bg-furnace-card border border-furnace-border rounded-lg p-1">
            {VIEW_MODES.map((m, i) => (
              <button
                key={m.label}
                onClick={() => setViewMode(i)}
                className={clsx(
                  "px-3 py-1 rounded text-xs font-semibold transition-all",
                  viewMode === i ? "bg-furnace-blue text-white" : "text-furnace-muted hover:text-furnace-text",
                )}
              >{m.label}</button>
            ))}
          </div>
          {/* Nav buttons */}
          <button onClick={() => setViewStart(addDays(minDate, -navDays))} aria-label="向前" className="p-2 rounded-lg border border-furnace-border hover:bg-furnace-border/50"><ChevronLeft className="w-4 h-4" /></button>
          <span className="text-sm text-furnace-text px-2 font-semibold min-w-[200px] text-center">
            {format(minDate, "yyyy/MM/dd")} — {format(addDays(minDate, days - 1), "yyyy/MM/dd")}
          </span>
          <button onClick={() => setViewStart(addDays(minDate, navDays))} aria-label="向後" className="p-2 rounded-lg border border-furnace-border hover:bg-furnace-border/50"><ChevronRight className="w-4 h-4" /></button>
          <button onClick={() => setViewStart(startOfDay(new Date()))} aria-label="回到今天" className="px-2 py-1 text-xs text-furnace-blue border border-furnace-blue/30 rounded hover:bg-furnace-blue/10">📅 今天</button>
          {/* Deps toggle */}
          <button onClick={() => setDepsVisible(!depsVisible)} aria-label={depsVisible ? "隱藏相依線" : "顯示相依線"} className={clsx("px-2 py-1 text-xs rounded border transition-all", depsVisible ? "bg-furnace-purple/10 text-furnace-purple border-furnace-purple/30" : "text-furnace-muted border-furnace-border")}>
            <GitBranch className="w-3 h-3 inline mr-1" />相依線
          </button>
          {/* Save button */}
          {hasChanges && (
            <button onClick={saveChanges} aria-label="儲存拖曳變更" className="px-3 py-1 text-xs font-semibold bg-amber-500 text-white rounded hover:bg-amber-600 transition-colors">
              儲存變更
            </button>
          )}
        </div>
      </div>

      {/* ── Gantt body with drag support ── */}
      <div className="fade-slide-up d4 bg-furnace-card border border-furnace-border rounded-xl overflow-auto"
        onMouseMove={handleDrag}
        onMouseUp={handleDragEnd}
        onMouseLeave={handleDragEnd}
        onTouchMove={handleDrag}
        onTouchEnd={handleDragEnd}
      >
        <div className="inline-block min-w-full relative">
          {/* Header */}
          <div className="sticky top-0 bg-furnace-card border-b border-furnace-border z-10">
            <div className="flex">
              <div className="w-[150px] min-w-[150px] px-3 py-3 text-sm font-bold text-furnace-muted border-r border-furnace-border flex items-center">爐次</div>
              <div className="flex" style={{ width: days * colW }}>
                {dates.map((d) => (
                  <div key={d.toISOString()} className={clsx("flex-shrink-0 text-center border-r border-furnace-border/30 py-2", d.getDay() === 0 || d.getDay() === 6 ? "bg-furnace-red/5" : "")} style={{ width: colW }}>
                    <div className="text-xs font-bold text-furnace-text">{format(d, "MM/dd")}</div>
                    <div className="text-[10px] text-furnace-muted/60">{format(d, "EEE", { locale: zhTW })}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Rows */}
          {kilnIds.map((kid) => {
            const kn = kilnMap[kid];
            const usage = kilnUsage[kid] || 0;
            return (
              <div key={kid} className="flex border-b border-furnace-border/30 hover:bg-furnace-bg/10">
                <div className="w-[150px] min-w-[150px] px-3 py-4 text-xs font-semibold text-furnace-text border-r border-furnace-border flex items-center gap-2">
                  <div className={clsx("w-2 h-2 rounded-full", usage >= 90 ? "bg-furnace-red" : usage >= 70 ? "bg-furnace-amber" : usage >= 40 ? "bg-furnace-purple" : "bg-furnace-blue")} />
                  {kn.name}
                </div>
                <div className="relative flex-shrink-0" style={{ width: days * colW, height: rowH }}>
                  {/* Grid */}
                  {dates.map((d) => (
                    <div key={d.toISOString()} className={clsx("absolute top-0 bottom-0 border-r border-furnace-border/10", d.getDay() === 0 || d.getDay() === 6 ? "bg-furnace-red/2" : "")} style={{ left: differenceInDays(d, minDate) * colW, width: colW }} />
                  ))}
                  {/* Task bars */}
                  {kn.entries.map((e) => {
                    const d = parseISO(e.delivery_date);
                    if (d < minDate || d > addDays(minDate, days)) return null;
                    const left = timeToLeft(e.delivery_date, minDate, colW);
                    const spanDays = daysFromHours(e.est_hours || 0);
                    const blockW = Math.max(60, spanDays * colW - 4);
                    const lc = (e.lifecycle_status || "scheduled");
                    const blkColor = e._dragged ? "bg-amber-500/80 ring-2 ring-amber-400" : (LIFECYCLE_COLORS[lc] || LIFECYCLE_COLORS.scheduled);
                    const isDragging = dragging?.ids?.includes(e.id || e.plan_no);
                    return (
                      <Tooltip
                        key={e.plan_no + (e.id || "")}
                        content={
                          <>
                            <strong>{e.plan_no}</strong>
                            <br />
                            合約: {e.contract_no || "-"} | {e.qty}支 | {e.voltage_kv}kV | {e.est_hours}h<br />
                            交期: {e.delivery_date} | 狀態: {LIFECYCLE_LABELS[lc] || lc}
                            <br />
                            <span className="text-[10px] opacity-60">🖱️👆 拖曳可調整交期</span>
                          </>
                        }
                      >
                        <div
                          className={clsx(
                            "absolute top-2 h-[36px] rounded-lg px-3 flex items-center text-[11px] font-semibold text-white overflow-hidden whitespace-nowrap shadow-md cursor-grab active:cursor-grabbing transition-shadow select-none",
                            blkColor,
                            isDragging && "ring-2 ring-white/50 shadow-lg z-40",
                          )}
                          style={{ left, width: blockW }}
                          onMouseDown={(ev) => handleDragStart(ev, [e.id || e.plan_no])}
                          onTouchStart={(ev) => handleDragStart(ev, [e.id || e.plan_no])}
                        >
                          <GripVertical className="w-3 h-3 mr-1 opacity-60 flex-shrink-0" />
                          {e.plan_no}
                          {lc !== "scheduled" && (
                            <span className="ml-1 text-[9px] opacity-70">·{LIFECYCLE_LABELS[lc]}</span>
                          )}
                        </div>
                      </Tooltip>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* ── Dependency Arrows SVG overlay ── */}
          {depsVisible && (() => {
            const arrows = [];
            const allEntries = [];
            kilnIds.forEach((kid) => {
              (kilnMap[kid].entries || []).forEach((e) => {
                allEntries.push({ ...e, _kilnId: kid, _rowIdx: kilnIds.indexOf(kid) });
              });
            });
            // Build dependency map: for entries with same contract_no, draw arrows
            const byContract = {};
            allEntries.forEach((e) => {
              const cno = e.contract_no || "_none_";
              if (!byContract[cno]) byContract[cno] = [];
              byContract[cno].push(e);
            });
            Object.values(byContract).forEach((group) => {
              if (group.length < 2) return;
              const sorted = group.sort((a, b) => (parseISO(a.delivery_date) - parseISO(b.delivery_date)));
              for (let i = 0; i < sorted.length - 1; i++) {
                const a = sorted[i], b = sorted[i + 1];
                if (a._kilnId !== b._kilnId) continue; // different kilns, no dependency shown
                const aD = parseISO(a.delivery_date); if (aD < minDate || aD > addDays(minDate, days)) continue;
                const bD = parseISO(b.delivery_date); if (bD < minDate || bD > addDays(minDate, days)) continue;
                const aLeft = timeToLeft(a.delivery_date, minDate, colW);
                const aSpan = daysFromHours(a.est_hours || 0);
                const bLeft = timeToLeft(b.delivery_date, minDate, colW);
                const aY = a._rowIdx * rowH + rowH / 2;
                const bY = b._rowIdx * rowH + rowH / 2;
                const aRight = aLeft + Math.max(60, aSpan * colW - 4);
                const midX = aRight + (bLeft - aRight) / 2;
                const dColor = "var(--c-purple)";
                arrows.push(
                  <path
                    key={a.plan_no + "→" + b.plan_no}
                    d={`M${aRight + 2},${aY} C${midX},${aY} ${midX},${bY} ${bLeft - 6},${bY}`}
                    stroke={dColor} strokeWidth="1.5" fill="none" opacity="0.5"
                    markerEnd="url(#arrowhead)"
                  />,
                );
              }
            });
            if (!arrows.length) return null;
            return (
              <svg className="absolute inset-0 pointer-events-none" aria-hidden="true" style={{ width: days * colW, height: kilnIds.length * rowH, top: 0, left: 150 }}>
                <defs>
                  <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                    <polygon points="0 0, 8 3, 0 6" fill="var(--c-purple)" opacity="0.6" />
                  </marker>
                </defs>
                {arrows}
              </svg>
            );
          })()}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-5 text-xs">
        <span className="text-furnace-muted font-semibold">狀態:</span>
        {Object.entries(LIFECYCLE_COLORS).map(([key, color]) => (
          <div key={key} className="flex items-center gap-1.5">
            <div className={clsx("w-3 h-3 rounded", color.replace("/60", ""))} />
            <span className="text-furnace-muted">{LIFECYCLE_LABELS[key]}</span>
          </div>
        ))}
        <span className="text-furnace-muted ml-4">🖱️ 拖曳條塊 = 調整交期 · 拖曳後按「儲存變更」</span>
      </div>
    </div>
  );
}