/**
 * ThemeToggle — per Stage 2 Design Contract
 *
 * Architecture:
 *   initTheme()     — runs before React render (main.jsx)
 *   toggleTheme()   — manual toggle, persists to localStorage
 *   getSystemTheme()— detect OS preference
 *   ThemeToggle     — UI component (Lucide icons, Sidebar footer)
 *
 * State flow:
 *   localStorage > matchMedia(dark) → data-theme attribute → CSS variables
 *
 * AC coverage: AC1(initTheme) AC2(toggle+pullst) AC3(global mq) AC5(data-theme attr) AC6(WCAG via CSS tokens)
 */
import { Sun, Moon } from "lucide-react";
import { useState } from "react";

const STORAGE_KEY = "theme";

/** Detect OS color scheme preference */
export function getSystemTheme() {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

/** Apply theme to <html data-theme>, called before React render */
export function initTheme() {
  const stored = localStorage.getItem(STORAGE_KEY);
  const system = getSystemTheme();
  const theme = stored || system;
  document.documentElement.setAttribute("data-theme", theme);
}

/** Manual toggle — flips theme and persists */
export function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem(STORAGE_KEY, next);
  return next;
}

/**
 * Global matchMedia listener (called from main.jsx).
 * Updates theme on OS change ONLY if user hasn't manually overridden.
 */
export function listenSystemTheme() {
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  const handler = (e) => {
    // Only auto-switch if user hasn't made a manual choice
    if (!localStorage.getItem(STORAGE_KEY)) {
      const next = e.matches ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", next);
    }
  };
  mq.addEventListener("change", handler);
  return () => mq.removeEventListener("change", handler);
}

/** UI Component — Sidebar footer toggle button */
export default function ThemeToggle() {
  const [theme, setTheme] = useState(() => {
    if (typeof window === "undefined") return "dark";
    return document.documentElement.getAttribute("data-theme") || "dark";
  });

  const handleToggle = () => {
    const next = toggleTheme();
    setTheme(next);
  };

  const isDark = theme === "dark";

  return (
    <button
      onClick={handleToggle}
      className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm transition-all w-full
                 text-furnace-muted hover:bg-furnace-border/50 hover:text-furnace-text"
      aria-label={isDark ? "切換至淺色模式" : "切換至深色模式"}
      title={isDark ? "切換至淺色模式" : "切換至深色模式"}
    >
      {isDark ? (
        <Sun className="w-[18px] h-[18px]" />
      ) : (
        <Moon className="w-[18px] h-[18px]" />
      )}
      深淺切換
    </button>
  );
}