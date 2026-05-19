import { Sun, Moon } from "lucide-react";
import { useState, useEffect } from "react";

const KEY = "furnace-theme";

export function getSystemTheme() {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

export function initTheme() {
  const stored = localStorage.getItem(KEY);
  const system = getSystemTheme();
  const theme = stored || system;
  document.documentElement.setAttribute("data-theme", theme);
}

export function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem(KEY, next);
  return next;
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState(() => {
    if (typeof window === "undefined") return "dark";
    return document.documentElement.getAttribute("data-theme") || "dark";
  });

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: light)");
    const handler = (e) => {
      if (!localStorage.getItem(KEY)) {
        const next = e.matches ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        setTheme(next);
      }
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const handleToggle = () => {
    const next = toggleTheme();
    setTheme(next);
  };

  const isLight = theme === "light";

  return (
    <button
      onClick={handleToggle}
      className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm transition-all w-full
                 text-furnace-muted hover:bg-furnace-border/50 hover:text-furnace-text"
      aria-label={isLight ? "切換至深色模式" : "切換至淺色模式"}
      title={isLight ? "切換至深色模式" : "切換至淺色模式"}
    >
      {isLight ? (
        <Moon className="w-[18px] h-[18px]" />
      ) : (
        <Sun className="w-[18px] h-[18px]" />
      )}
      深淺切換
    </button>
  );
}