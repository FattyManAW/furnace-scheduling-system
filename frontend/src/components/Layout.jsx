import { useState, useEffect, useCallback } from "react";
import { Menu, X, ChevronUp, WifiOff } from "lucide-react";
import Sidebar from "./Sidebar";
import ErrorBoundary from "./ErrorBoundary";

/** Offline detection banner — appears when navigator API reports offline */
function OfflineBanner() {
  const [offline, setOffline] = useState(
    typeof navigator !== "undefined" && !navigator.onLine,
  );

  useEffect(() => {
    const goOffline = () => setOffline(true);
    const goOnline = () => setOffline(false);
    window.addEventListener("offline", goOffline);
    window.addEventListener("online", goOnline);
    return () => {
      window.removeEventListener("offline", goOffline);
      window.removeEventListener("online", goOnline);
    };
  }, []);

  if (!offline) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[60] bg-furnace-amber/90 text-white text-sm font-semibold py-2 px-4 flex items-center justify-center gap-2">
      <WifiOff className="w-4 h-4" />
      目前為離線模式，部分功能可能受限
    </div>
  );
}

/** Back-to-top floating button — appears after 400px scroll */
function BackToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 400);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollTop = useCallback(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  if (!visible) return null;

  return (
    <button
      onClick={scrollTop}
      aria-label="回到頂端"
      className="fixed bottom-6 right-6 z-50 w-11 h-11 rounded-full bg-furnace-green text-white shadow-lg
                 flex items-center justify-center hover:bg-furnace-green/90 transition-all
                 animate-in-scale hover:scale-110 active:scale-95"
    >
      <ChevronUp className="w-5 h-5" />
    </button>
  );
}

export default function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Close sidebar on route change
  useEffect(() => {
    setSidebarOpen(false);
  }, [children]);

  // Close sidebar on escape
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") setSidebarOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="min-h-screen bg-furnace-bg text-furnace-text font-sans">
      <OfflineBanner />
      <div className="flex">
        {/* Desktop Sidebar */}
        <div className="hidden md:block">
          <Sidebar />
        </div>

        {/* Mobile overlay backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-40 md:hidden modal-backdrop"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Mobile sidebar drawer */}
        <div
          className={`fixed top-0 left-0 h-full w-[var(--c-sidebar-width)] z-50 transform md:hidden sidebar-slide ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}
        >
          <Sidebar onClose={() => setSidebarOpen(false)} />
        </div>

        {/* Main content */}
        <main className="flex-1 p-4 md:p-6 md:ml-[var(--c-sidebar-width)] min-h-screen">
          {/* Mobile header bar */}
          <div className="flex items-center gap-3 mb-4 md:hidden">
            <button
              onClick={() => setSidebarOpen(true)}
              aria-label="開啟選單"
              className="p-2 rounded-lg border border-furnace-border hover:bg-furnace-border/30"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="text-lg font-bold">排爐系統</div>
          </div>

          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>

      <BackToTop />
    </div>
  );
}