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
          // ══ Canonical Bridge (Christina token-map v4.2) ══
          // Opacity support via <alpha-value> + --c-*-rgb channels
          // bg-furnace-bg/20 → rgb(var(--c-bg-rgb) / 0.2) → works in all themes
          bg:      "rgb(var(--c-bg-rgb) / <alpha-value>)",
          card:    "rgb(var(--c-surface-rgb) / <alpha-value>)",
          border:  "var(--c-border)",
          hover:   "rgb(var(--c-elevated-rgb) / <alpha-value>)",
          text:    "var(--c-t2)",
          heading: "var(--c-t1)",
          muted:   "var(--c-t3)",

          // ── Semantic (rgb channels for opacity) ──
          blue:    "rgb(var(--c-teal-rgb) / <alpha-value>)",
          green:   "rgb(var(--c-success-rgb) / <alpha-value>)",
          amber:   "rgb(var(--c-warning-rgb) / <alpha-value>)",
          orange:  "rgb(var(--c-warning-rgb) / <alpha-value>)",
          red:     "rgb(var(--c-error-rgb) / <alpha-value>)",
          purple:  "rgb(var(--c-purple-rgb) / <alpha-value>)",
          cyan:    "rgb(var(--c-cyan-rgb) / <alpha-value>)",
        },
      },
    },
  },
  plugins: [],
}