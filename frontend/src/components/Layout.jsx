import Sidebar from "./Sidebar";

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-furnace-bg text-furnace-text font-sans">
      <div className="flex">
        <Sidebar />
        <main className="ml-[220px] flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
