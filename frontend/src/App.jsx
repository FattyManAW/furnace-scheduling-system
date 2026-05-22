import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Orders = lazy(() => import("./pages/Orders"));
const Molds = lazy(() => import("./pages/Molds"));
const Schedule = lazy(() => import("./pages/Schedule"));
const Gantt = lazy(() => import("./pages/Gantt"));
const Reports = lazy(() => import("./pages/Reports"));
const Settings = lazy(() => import("./pages/Settings"));

function PageFallback() {
  return <div className="flex items-center justify-center min-h-[60vh]">
    <div className="w-6 h-6 border-2 border-furnace-blue border-t-transparent rounded-full animate-spin" />
  </div>;
}

export default function App() {
  return (
    <Layout>
      <Suspense fallback={<PageFallback />}>
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
      </Suspense>
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
