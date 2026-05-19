import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { initTheme } from "./components/ThemeToggle.jsx";
import "./index.css";

// Apply theme before first render (avoids flash)
initTheme();

// ── 系統級 matchMedia 監聽 ──
// 不依賴 ThemeToggle 元件，全域監聽 OS 深淺色切換
const THEME_KEY = "furnace-theme";
if (typeof window !== "undefined") {
  const mq = window.matchMedia("(prefers-color-scheme: light)");
  const onSystemChange = (e) => {
    // 只在用戶未手動設定時跟隨系統
    if (!localStorage.getItem(THEME_KEY)) {
      const next = e.matches ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
    }
  };
  mq.addEventListener("change", onSystemChange);
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);