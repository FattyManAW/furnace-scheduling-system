import { AlertTriangle } from "lucide-react";
import { useEffect } from "react";

/**
 * ConfirmDialog — accessible modal alternative to window.confirm()
 * Usage:
 *   <ConfirmDialog open={showConfirm} title="確定刪除？" message="..." danger
 *     onConfirm={handleDelete} onCancel={() => setShowConfirm(false)} />
 */
export default function ConfirmDialog({
  open,
  title = "確認操作",
  message = "",
  confirmLabel = "確定",
  cancelLabel = "取消",
  danger = false,
  loading = false,
  onConfirm,
  onCancel,
}) {
  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === "Escape") onCancel?.(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-[60] modal-backdrop"
      onClick={onCancel}
      aria-hidden="true"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="modal-panel bg-furnace-card border border-furnace-border rounded-2xl p-6 w-full max-w-sm mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {danger && (
          <div className="w-11 h-11 rounded-full bg-furnace-red/10 flex items-center justify-center mb-4">
            <AlertTriangle className="w-5 h-5 text-furnace-red" />
          </div>
        )}
        <h3 className="text-lg font-bold text-furnace-text mb-1">{title}</h3>
        {message && <p className="text-sm text-furnace-muted mb-5">{message}</p>}
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 py-2.5 border border-furnace-border rounded-lg text-sm text-furnace-muted hover:text-furnace-text hover:bg-furnace-bg/50 transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={`flex-1 py-2.5 rounded-lg text-sm font-semibold text-white transition-colors ${
              danger
                ? "bg-furnace-red hover:bg-furnace-red/80"
                : "bg-furnace-green hover:bg-furnace-green/90"
            }${loading ? " opacity-50 cursor-wait" : ""}`}
          >
            {loading ? "處理中..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}