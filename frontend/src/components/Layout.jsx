import Sidebar from "./Sidebar";
import ErrorBoundary from "./ErrorBoundary";

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-furnace-bg text-furnace-text font-sans">
      <div className="flex">
        <Sidebar />
        <main className="ml-[var(--c-sidebar-width)] flex-1 p-6">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
