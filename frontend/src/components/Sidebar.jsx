import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  ClipboardList,
  Warehouse,
  Calendar,
  BarChart3,
  Kanban,
  Settings,
  Flame,
  Cog,
  X,
} from "lucide-react";
import ThemeToggle from "./ThemeToggle";
import { clsx } from "clsx";

const nav = [
  { to: "/", icon: LayoutDashboard, label: "儀表板" },
  { to: "/orders", icon: ClipboardList, label: "訂單管理" },
  { to: "/molds", icon: Warehouse, label: "模具庫存" },
  { to: "/schedule", icon: Calendar, label: "排程設定" },
  { to: "/gantt", icon: BarChart3, label: "甘特圖" },
  { to: "/kanban", icon: Kanban, label: "Kanban 看板" },
  { to: "/reports", icon: Settings, label: "報表匯出" },
  { to: "/settings", icon: Cog, label: "系統設定" },
];

export default function Sidebar({ onClose }) {
  const { pathname } = useLocation();

  return (
    <aside aria-label="主導覽欄" className="fixed left-0 top-0 h-screen w-[var(--c-sidebar-width)] bg-furnace-card border-r border-furnace-border flex flex-col z-50">
      {/* Mobile close button */}
      {onClose && (
        <button
          onClick={onClose}
          aria-label="關閉選單"
          className="md:hidden absolute top-3 right-3 p-2 rounded-lg hover:bg-furnace-border/50 text-furnace-muted"
        >
          <X className="w-5 h-5" />
        </button>
      )}
      {/* Logo */}
      <div className="p-5 border-b border-furnace-border">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-furnace-orange to-furnace-red flex items-center justify-center">
            <Flame className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-furnace-text leading-tight">
              排爐系統
            </h1>
            <p className="text-[10px] text-furnace-muted">Dry Bushing v2</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav aria-label="頁面導航" className="flex-1 p-3 space-y-1 overflow-y-auto">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            aria-current={({ isActive }) => (isActive ? "page" : undefined)}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group relative",
                isActive
                  ? "bg-furnace-green/15 text-furnace-green font-semibold"
                  : "text-furnace-muted hover:bg-furnace-border/50 hover:text-furnace-text",
              )
            }
          >
            <Icon className="w-[18px] h-[18px] transition-transform duration-200 group-hover:scale-110" />
            {label}
            {({ isActive }) =>
              isActive ? (
                <span className="absolute right-2 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-furnace-green shadow-[0_0_6px_var(--c-teal)]" />
              ) : null
            }
          </NavLink>
        ))}
      </nav>

      {/* Theme Toggle */}
      <div className="px-3 py-1 border-t border-furnace-border">
        <ThemeToggle />
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-furnace-border">
        <p className="text-[10px] text-furnace-muted text-center">
          干式套管最佳化排爐系統
        </p>
      </div>
    </aside>
  );
}
