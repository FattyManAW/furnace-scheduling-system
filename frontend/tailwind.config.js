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
          // ── Industrial Dark palette (ISA-101 + Apple Depth) ──
          bg:      "#181b23",   // 深灰底（絕非純黑）
          card:    "#22252f",   // 卡片層
          border:  "#2e3140",   // 邊框
          hover:   "#32364a",   // hover 層亮
          text:    "#e4e6ef",   // 主文字
          heading: "#f0f2f8",   // 標題文字
          muted:   "#747a8c",   // 次要文字（≥4.5:1 對比）

          // ── Semantic — 色彩節制（ISA-101: 僅用於狀態標記）──
          blue:    "#4b8cff",   // 主行動色
          green:   "#3cc97e",   // 正常/完成
          amber:   "#f0b028",   // 注意/等待
          red:     "#f44b55",   // 警報/逾期
          purple:  "#a78bfa",   // 輔助
          cyan:    "#38bdf8",   // 資訊
        },
      },
    },
  },
  plugins: [],
}