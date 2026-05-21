import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Orders from "./pages/Orders";
import Molds from "./pages/Molds";
import Schedule from "./pages/Schedule";
import Gantt from "./pages/Gantt";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/molds" element={<Molds />} />
        <Route path="/schedule" element={<Schedule />} />
        <Route path="/gantt" element={<Gantt />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}

function NotFound() {
  return (
    <div className="fade-slide-up d1 flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
      <p className="text-[28px] font-bold text-furnace-muted">404</p>
      <p className="text-furnace-muted">找不到此頁面</p>
      <a href="/" className="text-furnace-blue hover:text-furnace-blue/80 underline text-sm">
        返回儀表板
      </a>
    </div>
  );
}
