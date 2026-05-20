import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { initTheme, listenSystemTheme } from "./components/ThemeToggle.jsx";
import "./index.css";

// Stage 2 Design: initTheme before render (prevents flash — AC1, AC2)
initTheme();

// Stage 2 Design: global matchMedia listener (AC3: OS 即時更新 8 頁面)
listenSystemTheme();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);