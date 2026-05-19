/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        furnace: {
          // ══ Canonical Bridge (Christina token-map v3.2.1) ══
          // 所有 furnace-* class 現在引用 --c-* CSS variables
          // 雙主題 (dark/light) 自動切換，無需額外程式碼
          bg:      "var(--c-bg)",
          card:    "var(--c-surface)",
          border:  "var(--c-border)",
          hover:   "var(--c-elevated)",
          text:    "var(--c-t2)",
          heading: "var(--c-t1)",
          muted:   "var(--c-t3)",

          // ── Semantic ──
          blue:    "var(--c-teal)",
          green:   "var(--c-success)",
          amber:   "var(--c-warning)",
          red:     "var(--c-error)",
          purple:  "#a78bfa",   // Auxiliary (no canonical mapping)
          cyan:    "#38bdf8",   // Info (no canonical mapping)
        },
      },
    },
  },
  plugins: [],
}