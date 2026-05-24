/**
 * Skeleton — shared loading placeholder
 *
 * Usage:
 *   <Skeleton className="h-8 w-36" />  // inline block
 *   <PageSkeleton variant="dashboard" />  // per-page presets
 */

export function Skeleton({ className = "" }) {
  return <div className={`skeleton animate-pulse ${className}`} />;
}

/** Full-page skeleton — variant controls layout */
export function PageSkeleton({ variant = "table" }) {
  switch (variant) {
    case "dashboard":
      return (
        <div className="fade-slide-up d1 space-y-6" role="status" aria-label="載入中">
          <div>
            <Skeleton className="h-8 w-36 mb-2" />
            <Skeleton className="h-4 w-56" />
          </div>
          <div className="fade-slide-up d2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="fade-slide-up d2 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
                <Skeleton className="h-3 w-20 mb-3" />
                <Skeleton className="h-7 w-16 mb-2" />
                <Skeleton className="h-3 w-24" />
              </div>
            ))}
          </div>
          <div className="fade-slide-up d2 grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Skeleton className="h-48 rounded-xl" />
            <Skeleton className="h-48 rounded-xl" />
          </div>
          <span className="sr-only">儀表板資料載入中...</span>
        </div>
      );

    case "table":
      return (
        <div className="fade-slide-up d1 space-y-5" role="status" aria-label="載入中">
          <div>
            <Skeleton className="h-8 w-36 mb-2" />
            <Skeleton className="h-4 w-56" />
          </div>
          <div className="fade-slide-up d2 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-4">
            {[1, 2, 3, 4, 5, 6, 7].map((i) => (
              <div key={i} className="flex items-center gap-4 py-3 border-b border-furnace-border/30 last:border-0">
                <Skeleton className="h-4 w-8" />
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-4 w-20 ml-auto" />
                <Skeleton className="h-4 w-12" />
              </div>
            ))}
          </div>
          <span className="sr-only">表格資料載入中...</span>
        </div>
      );

    case "cards":
      return (
        <div className="fade-slide-up d1 space-y-5" role="status" aria-label="載入中">
          <div>
            <Skeleton className="h-8 w-36 mb-2" />
            <Skeleton className="h-4 w-56" />
          </div>
          <div className="fade-slide-up d2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="fade-slide-up d2 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
                <Skeleton className="h-5 w-28 mb-3" />
                <Skeleton className="h-3 w-full mb-2" />
                <Skeleton className="h-3 w-3/4 mb-2" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            ))}
          </div>
          <span className="sr-only">卡牌資料載入中...</span>
        </div>
      );

    default:
      return (
        <div className="fade-slide-up d1 space-y-4" role="status" aria-label="載入中">
          <Skeleton className="h-8 w-36" />
          <Skeleton className="h-48 w-full rounded-xl" />
        </div>
      );
  }
}

/** Empty state — icon + label + optional action */
export function EmptyState({
  icon: Icon,
  label = "尚無資料",
  hint = "",
  actionLabel = "",
  onAction,
}) {
  return (
    <div className="fade-slide-up d2 flex flex-col items-center justify-center py-16 text-center">
      {Icon && (
        <div className="w-14 h-14 rounded-2xl bg-furnace-border/30 flex items-center justify-center mb-4">
          <Icon className="w-7 h-7 text-furnace-muted" />
        </div>
      )}
      <p className="text-furnace-muted font-medium">{label}</p>
      {hint && <p className="text-furnace-muted text-xs mt-1.5 max-w-xs">{hint}</p>}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-4 px-4 py-2 bg-furnace-green text-white rounded-lg text-sm font-semibold hover:bg-furnace-green/90 transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}