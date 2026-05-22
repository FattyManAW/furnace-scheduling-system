import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { initTheme, listenSystemTheme } from "./components/ThemeToggle.jsx";
import { initScrollReveal } from "./lib/anim";
import "./index.css";

// Stage 2 Design: initTheme before render (prevents flash — AC1, AC2)
initTheme();

// Stage 2 Design: global matchMedia listener (AC3: OS 即時更新 8 頁面)
listenSystemTheme();

// Scroll-reveal animation observer (global, across all pages)
initScrollReveal();

// Dynamic <meta name="theme-color"> follows data-theme — browser chrome tint
(function syncThemeColor() {
  const el = document.querySelector('meta[name="theme-color"]');
  if (!el) return;
  const update = () => {
    const isDark =
      document.documentElement.getAttribute("data-theme") === "dark";
    const bgColor = getComputedStyle(document.documentElement).getPropertyValue("--c-bg").trim();
    el.setAttribute("content", bgColor);
  };
  update();
  new MutationObserver(update).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
})();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
