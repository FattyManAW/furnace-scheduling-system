import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";
import { clsx } from "clsx";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from "@dnd-kit/core";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import {
  GripVertical, Clock, AlertTriangle, CheckCircle2, XCircle,
  Play, Timer, Flag,
} from "lucide-react";
import { useToast } from "../components/Toast";
import { PageSkeleton } from "../components/Skeleton";

// ── State machine: valid transition map ─────────────────
const VALID_TRANSITIONS = {
  pending: ["scheduled", "cancelled"],
  scheduled: ["in_progress", "cancelled"],
  in_progress: ["completed", "blocked"],
  completed: [],
  cancelled: [],
  blocked: ["in_progress", "cancelled"],
};

const COLUMN_META = {
  pending: { label: "待排程", icon: Clock, color: "bg-furnace-muted/60" },
  scheduled: { label: "已排程", icon: Timer, color: "bg-furnace-blue/60" },
  in_progress: { label: "生產中", icon: Play, color: "bg-furnace-amber/60" },
  completed: { label: "已完成", icon: CheckCircle2, color: "bg-furnace-green/60" },
  cancelled: { label: "已取消", icon: XCircle, color: "bg-furnace-red/40" },
  blocked: { label: "已阻塞", icon: AlertTriangle, color: "bg-furnace-red/60" },
};

const PRIORITY_COLORS = {
  high: "border-l-furnace-red",
  medium: "border-l-furnace-amber",
  low: "border-l-furnace-muted",
};

const PRIORITY_LABELS = {
  high: "高",
  medium: "中",
  low: "低",
};

// ── Mock data — injected because GET /kanban returns items:[] ───
const MOCK_ITEMS = [
  { id: "MOCK-001", order_id: "SO-2026-0421", mold: "DB-32A 套管", priority: "high", due_date: "2026-05-10", status: "pending" },
  { id: "MOCK-002", order_id: "SO-2026-0418", mold: "DB-48B 法蘭", priority: "medium", due_date: "2026-05-15", status: "pending" },
  { id: "MOCK-003", order_id: "SO-2026-0405", mold: "DB-24C 彎頭", priority: "low", due_date: "2026-05-20", status: "pending" },
  { id: "MOCK-004", order_id: "SO-2026-0401", mold: "DB-32A 套管", priority: "high", due_date: "2026-05-05", status: "scheduled" },
  { id: "MOCK-005", order_id: "SO-2026-0403", mold: "DB-56A 接頭", priority: "medium", due_date: "2026-05-08", status: "scheduled" },
  { id: "MOCK-006", order_id: "SO-2026-0398", mold: "DB-32A 套管", priority: "high", due_date: "2026-05-02", status: "in_progress" },
  { id: "MOCK-007", order_id: "SO-2026-0395", mold: "DB-48B 法蘭", priority: "high", due_date: "2026-05-03", status: "in_progress" },
  { id: "MOCK-008", order_id: "SO-2026-0389", mold: "DB-24C 彎頭", priority: "medium", due_date: "2026-04-28", status: "in_progress" },
  { id: "MOCK-009", order_id: "SO-2026-0372", mold: "DB-56A 接頭", priority: "high", due_date: "2026-04-15", status: "completed" },
  { id: "MOCK-010", order_id: "SO-2026-0368", mold: "DB-32A 套管", priority: "low", due_date: "2026-04-10", status: "completed" },
  { id: "MOCK-011", order_id: "SO-2026-0355", mold: "DB-48B 法蘭", priority: "medium", due_date: "2026-05-01", status: "blocked" },
  { id: "MOCK-012", order_id: "SO-2026-0425", mold: "DB-24C 彎頭", priority: "high", due_date: "2026-05-22", status: "pending" },
  { id: "MOCK-013", order_id: "SO-2026-0410", mold: "DB-56A 接頭", priority: "low", due_date: "2026-05-12", status: "scheduled" },
  { id: "MOCK-014", order_id: "SO-2026-0330", mold: "DB-32A 套管", priority: "medium", due_date: "2026-04-01", status: "completed" },
  { id: "MOCK-015", order_id: "SO-2026-0440", mold: "DB-48B 法蘭", priority: "high", due_date: "2026-05-25", status: "pending" },
];

// ── Kanban Card ────────────────────────────────
function KanbanCard({ item, isDragging }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: item.id,
    data: { item },
  });

  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)`, zIndex: 50 }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={style}
      role="button"
      tabIndex={0}
      aria-label={`${item.order_id} - ${item.mold}`}
      className={clsx(
        "group bg-furnace-card border border-furnace-border rounded-lg p-3 cursor-grab active:cursor-grabbing",
        "transition-all duration-150 hover:shadow-md hover:border-furnace-blue/40",
        "border-l-[3px]",
        PRIORITY_COLORS[item.priority] || "border-l-furnace-muted",
        isDragging && "opacity-50 shadow-lg",
      )}
    >
      {/* Drag handle */}
      <div className="flex items-center gap-2 mb-2">
        <GripVertical className="w-3.5 h-3.5 text-furnace-muted/60 group-hover:text-furnace-muted shrink-0" />
        <span className="text-sm font-semibold text-furnace-text truncate">{item.order_id}</span>
      </div>

      {/* Mold name */}
      <p className="text-xs text-furnace-muted mb-2 truncate">{item.mold}</p>

      {/* Footer: priority + due date */}
      <div className="flex items-center justify-between text-[10px]">
        <span className={clsx(
          "px-1.5 py-0.5 rounded font-medium",
          item.priority === "high" && "bg-furnace-red/15 text-furnace-red",
          item.priority === "medium" && "bg-furnace-amber/15 text-furnace-amber",
          item.priority === "low" && "bg-furnace-border/40 text-furnace-muted",
        )}>
          {PRIORITY_LABELS[item.priority] || item.priority}
        </span>
        <span className="text-furnace-muted flex items-center gap-1">
          <Flag className="w-2.5 h-2.5" />
          {item.due_date}
        </span>
      </div>
    </div>
  );
}

// ── Kanban Column ──────────────────────────────
function KanbanColumn({ columnId, items, activeItem }) {
  const { setNodeRef, isOver } = useDroppable({ id: columnId });
  const meta = COLUMN_META[columnId] || { label: columnId, icon: Clock, color: "bg-furnace-muted" };
  const Icon = meta.icon;

  // Determine if dropping here is valid for the active item
  const isValidDrop = activeItem
    ? VALID_TRANSITIONS[activeItem.status]?.includes(columnId) || activeItem.status === columnId
    : true;

  return (
    <div className="flex flex-col min-w-[220px] max-w-[260px] flex-1">
      {/* Column header */}
      <div className="flex items-center gap-2 mb-3 px-1">
        <div className={clsx("w-2.5 h-2.5 rounded-full", meta.color)} />
        <Icon className="w-4 h-4 text-furnace-muted" />
        <h3 className="text-sm font-semibold text-furnace-text">{meta.label}</h3>
        <span className="ml-auto text-xs text-furnace-muted bg-furnace-border/30 px-1.5 py-0.5 rounded-full">
          {items.length}
        </span>
      </div>

      {/* Drop zone */}
      <div
        ref={setNodeRef}
        className={clsx(
          "flex flex-col gap-2 p-2 rounded-xl min-h-[300px] transition-colors duration-200",
          "border border-transparent",
          isOver && isValidDrop && "border-furnace-blue/40 bg-furnace-blue/5",
          isOver && !isValidDrop && "border-furnace-red/40 bg-furnace-red/5",
        )}
      >
        {items.map((item) => (
          <KanbanCard key={item.id} item={item} isDragging={activeItem?.id === item.id} />
        ))}

        {/* Empty state */}
        {items.length === 0 && (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-xs text-furnace-muted/50 text-center">
              {isOver && isValidDrop ? "放置至此" : "尚無訂單"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Drag overlay (the card that follows cursor) ──
function DragCard({ item }) {
  return (
    <div className="bg-furnace-card border border-furnace-blue/60 rounded-lg p-3 shadow-xl rotate-2 border-l-[3px] border-l-furnace-blue">
      <div className="flex items-center gap-2 mb-2">
        <GripVertical className="w-3.5 h-3.5 text-furnace-muted shrink-0" />
        <span className="text-sm font-semibold text-furnace-text">{item.order_id}</span>
      </div>
      <p className="text-xs text-furnace-muted mb-2">{item.mold}</p>
    </div>
  );
}

// ── Main Kanban Page ───────────────────────────
export default function Kanban() {
  const [items, setItems] = useState([]);
  const [activeItem, setActiveItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { addToast } = useToast();

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  );

  // ── Load data ─────────────────────────────
  // ── Priority sort helper (DRY) ─────────
  const sortByPriority = (arr) => {
    const order = { high: 0, medium: 1, low: 2 };
    return [...arr].sort((a, b) => (order[a.priority] || 2) - (order[b.priority] || 2));
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getKanban();
      // Use API items + inject mocks
      const merged = [...(data.items || [])];
      if (merged.length === 0) {
        merged.push(...MOCK_ITEMS);
      }
      setItems(sortByPriority(merged));
    } catch (e) {
      setError(e.message);
      // Fallback: use all mock data
      setItems(sortByPriority(MOCK_ITEMS));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // ── Columns grouped from items ────────────
  const columns = COLUMN_META;
  const columnIds = Object.keys(columns);
  const itemsByColumn = {};
  columnIds.forEach((cid) => {
    itemsByColumn[cid] = items.filter((i) => i.status === cid);
  });

  // ── Drag handlers ────────────────────────
  const handleDragStart = useCallback((event) => {
    const { active } = event;
    const item = items.find((i) => i.id === active.id);
    setActiveItem(item || null);
  }, [items]);

  const handleDragEnd = useCallback(async (event) => {
    const { active, over } = event;
    setActiveItem(null);

    if (!over) return; // Dropped outside

    const targetColumn = over.id; // column droppable id
    const draggedItem = items.find((i) => i.id === active.id);
    if (!draggedItem) return;

    // Same column — no-op
    if (draggedItem.status === targetColumn) return;

    // Validate transition
    const valid = VALID_TRANSITIONS[draggedItem.status] || [];
    if (!valid.includes(targetColumn)) {
      addToast(
        `無法將「${COLUMN_META[draggedItem.status]?.label || draggedItem.status}」直接移至「${COLUMN_META[targetColumn]?.label || targetColumn}」`,
        "warning",
      );
      return;
    }

    // Optimistic update
    const prevItems = [...items];
    setItems((prev) =>
      prev.map((i) => (i.id === draggedItem.id ? { ...i, status: targetColumn } : i)),
    );

    // API call
    try {
      await api.updateKanbanItem(draggedItem.id, targetColumn);
    } catch (e) {
      // Rollback on failure (422 or network)
      setItems(prevItems);
      addToast(
        `移動失敗：${e.message || "狀態轉換不合法"}`,
        "error",
      );
    }
  }, [items, addToast]);

  const handleDragCancel = useCallback(() => {
    setActiveItem(null);
  }, []);

  // ── Loading state ─────────────────────────
  if (loading) return <PageSkeleton />;

  // ── Error banner ──────────────────────────
  if (error && items.length === 0) {
    return (
      <div className="fade-slide-up d1 space-y-4">
        <div className="bg-furnace-red/10 border border-furnace-red/30 rounded-xl p-4" role="alert">
          <p className="text-sm text-furnace-red font-medium">載入失敗：{error}</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-furnace-blue text-white rounded-lg text-sm hover:bg-furnace-blue/90 transition-colors"
        >
          重試
        </button>
      </div>
    );
  }

  // ── Main render ───────────────────────────
  return (
    <div className="fade-slide-up d1 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-furnace-text">Kanban 看板</h2>
          <p className="text-xs text-furnace-muted mt-0.5">
            拖曳卡片變更訂單狀態 · 共 {items.length} 筆訂單
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-3 py-1.5 text-xs rounded-lg border border-furnace-border text-furnace-muted hover:text-furnace-text hover:border-furnace-text/30 transition-colors"
        >
          重新整理
        </button>
      </div>

      {/* Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <div className="flex gap-3 overflow-x-auto pb-4 -mx-2 px-2 scrollbar-thin">
          {columnIds.map((colId) => (
            <KanbanColumn
              key={colId}
              columnId={colId}
              items={itemsByColumn[colId] || []}
              activeItem={activeItem}
            />
          ))}
        </div>

        <DragOverlay>
          {activeItem ? <DragCard item={activeItem} /> : null}
        </DragOverlay>
      </DndContext>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-[10px] text-furnace-muted pt-3 border-t border-furnace-border">
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full border-l-2 border-l-furnace-red" /> 高優先
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full border-l-2 border-l-furnace-amber" /> 中優先
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full border-l-2 border-l-furnace-muted" /> 低優先
        </span>
        <span className="ml-2">· 拖曳至目標欄位變更狀態</span>
        <span className="ml-2 text-furnace-muted/50">Mock 資料模式（後端 items 為空）</span>
      </div>
    </div>
  );
}