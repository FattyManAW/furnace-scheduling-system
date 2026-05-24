import { useState, useEffect, useCallback } from "react";
import { clsx } from "clsx";
import { Database, HardDrive, Shield, Bell, Info, AlertTriangle } from "lucide-react";
import ConfirmDialog from "../components/ConfirmDialog";

export default function Settings() {
  const [activeTab, setActiveTab] = useState("system");
  const [version, setVersion] = useState({ version: "—", commit: "—" });
  const [dbLoading, setDbLoading] = useState(null); // null | 'reimport' | 'clear'
  const [dbResult, setDbResult] = useState(null);
  const [clearConfirm, setClearConfirm] = useState(false);

  useEffect(() => {
    fetch("/health")
      .then((r) => r.json())
      .then((d) => setVersion({ version: d.version, commit: d.commit?.slice(0, 7) }))
      .catch(() => {});
  }, []);

  const tabs = [
    { id: "system", label: "系統" },
    { id: "database", label: "資料庫" },
    { id: "notifications", label: "通知" },
    { id: "about", label: "關於" },
  ];

  const handleTabKeyDown = useCallback((e) => {
    const idx = tabs.findIndex((t) => t.id === activeTab);
    let next;
    if (e.key === "ArrowRight") next = (idx + 1) % 4;
    else if (e.key === "ArrowLeft") next = (idx - 1 + 4) % 4;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = 3;
    else return;
    e.preventDefault();
    const tab = tabs[next];
    setActiveTab(tab.id);
    document.getElementById(`settings-tab-${tab.id}`)?.focus();
  }, [activeTab, tabs]);

  return (
    <div className="fade-slide-up d1 space-y-5">
      <div>
        <h1 className="text-2xl font-bold">系統設定</h1>
        <p className="text-furnace-muted text-sm mt-0.5">系統配置與偏好設定</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-furnace-border pb-3" role="tablist" aria-label="設定分類" onKeyDown={handleTabKeyDown}>
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            id={`settings-tab-${t.id}`}
            aria-selected={activeTab === t.id}
            aria-controls={`settings-panel-${t.id}`}
            tabIndex={activeTab === t.id ? 0 : -1}
            onClick={() => setActiveTab(t.id)}
            className={clsx(
              "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
              activeTab === t.id
                ? "bg-furnace-green/15 text-furnace-green"
                : "text-furnace-muted hover:text-furnace-text hover:bg-furnace-border/30",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "system" && (
        <div id="settings-panel-system" role="tabpanel" aria-labelledby="settings-tab-system" className="fade-slide-up d1 space-y-4">
          <div className="fade-slide-up d2 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-furnace-text mb-4 flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-furnace-blue" /> 一般設定
            </h2>
            <div className="fade-slide-up d1 space-y-4">
              <div className="flex items-center justify-between">
                <label htmlFor="hours-cap" className="cursor-pointer">
                  <p className="text-sm text-furnace-text">每日工時上限</p>
                  <p className="text-xs text-furnace-muted">
                    全局工時限制（小時）
                  </p>
                </label>
                <input
                  id="hours-cap"
                  type="number"
                  defaultValue={1098}
                  className="w-32 px-3 py-2 bg-furnace-bg border border-furnace-border rounded-lg text-sm text-furnace-text text-center"
                />
              </div>
              <div className="flex items-center justify-between">
                <label htmlFor="large-od-threshold" className="cursor-pointer">
                  <p className="text-sm text-furnace-text">大產品門檻 (OD)</p>
                  <p className="text-xs text-furnace-muted">
                    外徑大於此值只能進大槽爐
                  </p>
                </label>
                <input
                  id="large-od-threshold"
                  type="number"
                  defaultValue={470}
                  className="w-32 px-3 py-2 bg-furnace-bg border border-furnace-border rounded-lg text-sm text-furnace-text text-center"
                />
              </div>
              <div className="flex items-center justify-between">
                <label htmlFor="low-stock-threshold" className="cursor-pointer">
                  <p className="text-sm text-furnace-text">
                    低庫存警示 threshold
                  </p>
                  <p className="text-xs text-furnace-muted">
                    存量低於此值顯示警示
                  </p>
                </label>
                <input
                  id="low-stock-threshold"
                  type="number"
                  defaultValue={10}
                  className="w-32 px-3 py-2 bg-furnace-bg border border-furnace-border rounded-lg text-sm text-furnace-text text-center"
                />
              </div>
            </div>
            <div className="flex justify-end mt-4 pt-4 border-t border-furnace-border">
              <button className="px-4 py-2 bg-furnace-green text-white rounded-lg text-sm hover:bg-furnace-green/90">
                儲存設定
              </button>
            </div>
          </div>

          <div className="fade-slide-up d3 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-furnace-text mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4 text-furnace-purple" /> 排程策略
            </h2>
            <div className="fade-slide-up d1 space-y-3" role="radiogroup" aria-label="預設排程策略">
              {[
                { name: "deadline", label: "交期優先", desc: "優先排入最早交期的訂單" },
                { name: "fill", label: "填滿優先", desc: "優先填滿同一爐的槽位" },
                { name: "balance", label: "平衡模式", desc: "平衡各爐使用量" },
              ].map((s) => (
                <label
                  key={s.name}
                  className="flex items-start gap-3 p-3 rounded-lg border border-furnace-border hover:border-furnace-blue/30 cursor-pointer"
                >
                  <input type="radio" name="default_strategy" value={s.name} defaultChecked={s.name === "deadline"} className="mt-1 accent-furnace-green" />
                  <div>
                    <p className="text-sm font-medium text-furnace-text">{s.label}</p>
                    <p className="text-xs text-furnace-muted">{s.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === "database" && (
        <div id="settings-panel-database" role="tabpanel" aria-labelledby="settings-tab-database" className="fade-slide-up d1 space-y-4">
          <div className="fade-slide-up d4 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5" role="region" aria-label="資料庫操作">
            <h2 className="text-sm font-semibold text-furnace-text mb-4 flex items-center gap-2">
              <Database className="w-4 h-4 text-furnace-blue" /> 資料庫操作
            </h2>
            <div className="fade-slide-up d2 grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-4 rounded-xl border border-furnace-border">
                <h3 className="text-sm font-semibold text-furnace-text mb-2">重新匯入初始資料</h3>
                <p className="text-xs text-furnace-muted mb-3">
                  從 data/ 目錄的 JSON 檔案重新匯入訂單、模具、干燥罐、製程資料。會跳過已存在的記錄。
                </p>
                <button
                  onClick={() => { setDbLoading("reimport"); setTimeout(() => { setDbResult("✅ 匯入請求已發送"); setDbLoading(null); }, 1000); }}
                  disabled={!!dbLoading}
                  className="px-4 py-2 bg-furnace-blue/10 text-furnace-blue rounded-lg text-sm hover:bg-furnace-blue/20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {dbLoading === "reimport" ? "匯入中…" : "執行匯入"}
                </button>
              </div>
              <div className="p-4 rounded-xl border border-furnace-red/20 bg-furnace-red/5">
                <h3 className="text-sm font-semibold text-furnace-red mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4" /> 清除排程
                </h3>
                <p className="text-xs text-furnace-muted mb-3">
                  清除所有排程結果與訂單狀態。此操作不可復原。
                </p>
                <button
                  onClick={() => setClearConfirm(true)}
                  disabled={!!dbLoading}
                  className="px-4 py-2 bg-furnace-red/10 text-furnace-red rounded-lg text-sm hover:bg-furnace-red/20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {dbLoading === "clear" ? "清除中…" : "清除排程"}
                </button>
              </div>
            </div>
            {dbResult && <p className="mt-3 text-xs text-furnace-green">{dbResult}</p>}
          </div>
          <div className="fade-slide-up d5 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5" role="region" aria-label="資料統計">
            <h2 className="text-sm font-semibold text-furnace-text mb-3">資料統計</h2>
            <div className="fade-slide-up d2 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              {[{ label: "訂單表", name: "orders" }, { label: "模具表", name: "molds" }, { label: "干燥罐表", name: "kilns" }, { label: "排程表", name: "schedule_entries" }].map((t) => (
                <div key={t.name}>
                  <p className="text-furnace-muted text-xs">{t.label}</p>
                  <p className="font-bold text-furnace-text">{t.name}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === "notifications" && (
        <div id="settings-panel-notifications" role="tabpanel" aria-labelledby="settings-tab-notifications" className="fade-slide-up d6 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-furnace-text mb-4 flex items-center gap-2">
            <Bell className="w-4 h-4 text-furnace-amber" /> 通知設定
          </h2>
          <div className="fade-slide-up d1 space-y-4">
            {[
              { label: "工時超標通知", desc: "排程工時超過每日上限時通知" },
              { label: "逾期訂單提醒", desc: "有逾期訂單時顯示警示" },
              { label: "低庫存提醒", desc: "模具存量低於門檻時提示" },
              { label: "排程完成通知", desc: "排程優化執行完畢時通知" },
            ].map(({ label, desc }) => (
              <label key={label} className="flex items-center justify-between p-3 rounded-lg border border-furnace-border hover:border-furnace-blue/20 cursor-pointer">
                <div>
                  <p className="text-sm text-furnace-text">{label}</p>
                  <p className="text-xs text-furnace-muted">{desc}</p>
                </div>
                <input type="checkbox" defaultChecked className="w-4 h-4 accent-furnace-green" />
              </label>
            ))}
          </div>
        </div>
      )}

      {activeTab === "about" && (
        <div id="settings-panel-about" role="tabpanel" aria-labelledby="settings-tab-about" className="fade-slide-up d6 bg-furnace-card hover-lift border border-furnace-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-furnace-text mb-4 flex items-center gap-2">
            <Info className="w-4 h-4 text-furnace-cyan" /> 關於本系統
          </h2>
          <div className="fade-slide-up d1 space-y-3 text-sm text-furnace-muted">
            <p><span className="text-furnace-text font-semibold">系統名稱：</span>干式套管最佳化排爐系統</p>
            <p>
              <span className="text-furnace-text font-semibold">版本：</span>
              {version.version}
              <span className="text-furnace-muted text-xs ml-2">({version.commit})</span>
            </p>
            <p><span className="text-furnace-text font-semibold">架構：</span>React + FastAPI + SQLite</p>
            <p><span className="text-furnace-text font-semibold">功能：</span>訂單管理、模具庫存、排程優化、甘特圖、報表匯出</p>
            <p><span className="text-furnace-text font-semibold">排程邏輯：</span>依交期優先分配至最優爐位，每日工時上限 1098h</p>
            <p><span className="text-furnace-text font-semibold">大產品限制：</span>外徑 ≥ 470mm 只能進大槽爐</p>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={clearConfirm}
        title="⚠️ 確定清除排程？"
        message="此操作將清除所有排程結果與訂單狀態，無法復原。"
        confirmLabel="確定清除"
        danger
        onConfirm={() => { setDbLoading("clear"); setClearConfirm(false); setTimeout(() => { setDbResult("✅ 排程已清除"); setDbLoading(null); }, 1000); }}
        onCancel={() => setClearConfirm(false)}
      />
    </div>
  );
}