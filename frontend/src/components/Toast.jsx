import { createContext, useContext, useState, useCallback, useEffect, useRef } from "react";
import { CheckCircle, AlertTriangle, XCircle, Info, X } from "lucide-react";

const ToastContext = createContext(null);

const ICONS = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const TOAST_TIMEOUT = 5000;

let toastId = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timersRef = useRef({});

  const remove = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    if (timersRef.current[id]) {
      clearTimeout(timersRef.current[id]);
      delete timersRef.current[id];
    }
  }, []);

  const add = useCallback((message, type = "info", duration = TOAST_TIMEOUT) => {
    const id = ++toastId;
    setToasts((prev) => [...prev.slice(-4), { id, message, type }]);
    if (duration > 0) {
      timersRef.current[id] = setTimeout(() => remove(id), duration);
    }
    return id;
  }, [remove]);

  const toast = useCallback(
    (message, opts) => add(message, opts?.type, opts?.duration),
    [add],
  );
  toast.success = (msg, dur) => add(msg, "success", dur);
  toast.error = (msg, dur) => add(msg, "error", dur);
  toast.warning = (msg, dur) => add(msg, "warning", dur);
  toast.info = (msg, dur) => add(msg, "info", dur);

  useEffect(() => {
    return () => {
      Object.values(timersRef.current).forEach(clearTimeout);
    };
  }, []);

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      >
        {toasts.map((t) => {
          const Icon = ICONS[t.type] || Info;
          const borderMap = {
            success: "border-furnace-green",
            error: "border-furnace-red",
            warning: "border-furnace-amber",
            info: "border-furnace-blue",
          };
          return (
            <div
              key={t.id}
              role="alert"
              className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl border-l-4 bg-furnace-card border border-furnace-border ${borderMap[t.type]} shadow-lg toast-enter`}
            >
              <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: `var(--c-${t.type === 'info' ? 'teal' : t.type === 'error' ? 'error' : t.type === 'warning' ? 'warning' : 'success'})` }} />
              <p className="text-sm text-furnace-text flex-1">{t.message}</p>
              <button
                onClick={() => remove(t.id)}
                aria-label="關閉通知"
                className="flex-shrink-0 text-furnace-muted hover:text-furnace-text transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}