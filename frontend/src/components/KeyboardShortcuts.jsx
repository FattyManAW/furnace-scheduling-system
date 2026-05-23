import { useEffect, useCallback, useState } from "react";
import { Search, Command, X, Keyboard } from "lucide-react";
import { useNavigate } from "react-router-dom";

/** ⌘K / ⌘/ / Esc — global keyboard shortcuts overlay */
export default function KeyboardShortcuts() {
  const navigate = useNavigate();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const PAGES = [
    { label: "儀表板", path: "/", key: "1" },
    { label: "訂單管理", path: "/orders", key: "2" },
    { label: "模具管理", path: "/molds", key: "3" },
    { label: "排程", path: "/schedule", key: "4" },
    { label: "甘特圖", path: "/gantt", key: "5" },
    { label: "報表", path: "/reports", key: "6" },
    { label: "設定", path: "/settings", key: "7" },
  ];

  const filtered = searchQuery
    ? PAGES.filter((p) => p.label.toLowerCase().includes(searchQuery.toLowerCase()))
    : PAGES;

  const onKeyDown = useCallback(
    (e) => {
      // ⌘K / Ctrl+K → command palette
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setPaletteOpen((p) => !p);
        setSearchQuery("");
      }
      // ⌘/ / Ctrl+/ → shortcut help
      if ((e.metaKey || e.ctrlKey) && e.key === "/") {
        e.preventDefault();
        setPaletteOpen(true);
        setSearchQuery("");
      }
      // Esc → close palette
      if (e.key === "Escape" && paletteOpen) {
        e.preventDefault();
        setPaletteOpen(false);
        setSearchQuery("");
      }
      // Number keys in palette
      if (paletteOpen && e.key >= "1" && e.key <= "7" && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        const idx = parseInt(e.key, 10) - 1;
        if (filtered[idx]) {
          navigate(filtered[idx].path);
          setPaletteOpen(false);
          setSearchQuery("");
        }
      }
      // Enter to select first match
      if (paletteOpen && e.key === "Enter" && filtered.length > 0) {
        e.preventDefault();
        navigate(filtered[0].path);
        setPaletteOpen(false);
        setSearchQuery("");
      }
      // Arrow keys
      if (paletteOpen && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
        e.preventDefault();
      }
    },
    [paletteOpen, navigate, filtered],
  );

  useEffect(() => {
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onKeyDown]);

  if (!paletteOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 z-[90] modal-backdrop"
        onClick={() => setPaletteOpen(false)}
      />
      {/* Palette */}
      <div
        role="dialog"
        aria-label="頁面導航"
        className="fixed top-[15%] left-1/2 -translate-x-1/2 z-[100] w-full max-w-md bg-furnace-card rounded-2xl shadow-2xl border border-furnace-border overflow-hidden"
      >
        {/* Search input */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-furnace-border">
          <Search className="w-4 h-4 text-furnace-muted" />
          <input
            autoFocus
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜尋頁面..."
            className="flex-1 bg-transparent text-furnace-text text-sm outline-none placeholder:text-furnace-muted"
          />
          <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-furnace-elevated text-furnace-muted font-mono">
            esc
          </kbd>
        </div>
        {/* Page list */}
        <div className="max-h-64 overflow-y-auto py-1">
          {filtered.length === 0 ? (
            <p className="px-4 py-6 text-center text-sm text-furnace-muted">無符合頁面</p>
          ) : (
            filtered.map((p, i) => (
              <button
                key={p.path}
                onClick={() => {
                  navigate(p.path);
                  setPaletteOpen(false);
                  setSearchQuery("");
                }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-furnace-text hover:bg-furnace-blue/10 transition-colors text-left"
              >
                <span className="flex-1">{p.label}</span>
                <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-furnace-elevated text-furnace-muted font-mono">
                  {p.key}
                </kbd>
              </button>
            ))
          )}
        </div>
        {/* Hint footer */}
        <div className="flex items-center gap-2 px-4 py-2 border-t border-furnace-border text-[10px] text-furnace-muted">
          <Command className="w-3 h-3" />
          <span>
            <kbd className="px-1 py-0.5 rounded bg-furnace-elevated font-mono">K</kbd> 導航選單
            {" · "}
            <kbd className="px-1 py-0.5 rounded bg-furnace-elevated font-mono">1-7</kbd> 快速跳頁
            {" · "}
            <kbd className="px-1 py-0.5 rounded bg-furnace-elevated font-mono">Esc</kbd> 關閉
          </span>
        </div>
      </div>
    </>
  );
}