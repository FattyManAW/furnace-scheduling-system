import { Sun, Moon, Monitor } from "lucide-react";
import { useState, useEffect, useCallback } from "react";

const KEY = "furnace-theme";
const CYCLE = ["auto", "light", "dark"];

const LABELS = { auto: "跟隨系統", light: "淺色模式", dark: "深色模式" };
const ICONS = { auto: Monitor, light: Sun, dark: Moon };

export function getSystemTheme() {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function resolveTheme(stored) {
  if (stored && CYCLE.includes(stored)) return stored;
  if (stored === "light" || stored === "dark") return stored;
  return "auto";
}

export function initTheme() {
  const stored = localStorage.getItem(KEY);
  const mode = resolveTheme(stored);
  const actual = mode === "auto" ? getSystemTheme() : mode;
  document.documentElement.setAttribute("data-theme", actual);
  if (!stored) localStorage.setItem(KEY, "auto");
}

export default function ThemeToggle() {
  const [mode, setMode] = useState(() => {
    if (typeof window === "undefined") return "dark";
    return resolveTheme(localStorage.getItem(KEY));
  });

  const apply = useCallback((m) => {
    const actual = m === "auto" ? getSystemTheme() : m;
    document.documentElement.setAttribute("data-theme", actual);
    localStorage.setItem(KEY, m);
    setMode(m);
  }, []);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: light)");
    const handler = (e) => {
      const currentMode = localStorage.getItem(KEY);
      if (!currentMode || currentMode === "auto") {
        const actual = e.matches ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", actual);
        if (currentMode === "auto") setMode("auto");
      }
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const handleToggle = () => {
    const idx = CYCLE.indexOf(mode);
    const next = CYCLE[(idx + 1) % CYCLE.length];
    apply(next);
  };

  const Icon = ICONS[mode];

  return (
    <button
      onClick={handleToggle}
      className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm transition-all w-full
                 text-furnace-muted hover:bg-furnace-border/50 hover:text-furnace-text"
      aria-label={`主題：${LABELS[mode]} — 點擊切換`}
      title={`主題：${LABELS[mode]} — 點擊切換`}
    >
      <Icon className="w-[18px] h-[18px]" />
      {LABELS[mode]}
    </button>
  );
}