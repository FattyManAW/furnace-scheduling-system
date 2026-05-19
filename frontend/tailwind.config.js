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
          bg: "#0f1117",
          card: "#1a1d27",
          border: "#2a2d3a",
          text: "#e2e8f0",
          muted: "#8892a4",
          blue: "#3b82f6",
          green: "#10b981",
          orange: "#f59e0b",
          red: "#ef4444",
          purple: "#8b5cf6",
          cyan: "#06b6d4",
        },
      },
    },
  },
  plugins: [],
}
