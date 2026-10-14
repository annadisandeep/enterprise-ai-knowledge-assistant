import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { CheckCircle2, XCircle, X } from "lucide-react";
import { uid } from "../lib/utils";

type ToastKind = "success" | "error";
interface Toast {
  id: string;
  kind: ToastKind;
  message: string;
}

interface ToastContextValue {
  notify: (kind: ToastKind, message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

// eslint-disable-next-line react-refresh/only-export-components -- hook co-located with its provider by design
export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const notify = useCallback(
    (kind: ToastKind, message: string) => {
      const id = uid("toast");
      setToasts((t) => [...t, { id, kind, message }]);
      window.setTimeout(() => dismiss(id), 5000);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
        aria-live="assertive"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            role="alert"
            className="card flex items-start gap-3 p-3 animate-fade-in"
          >
            {t.kind === "success" ? (
              <CheckCircle2 className="mt-0.5 h-5 w-5 flex-none text-green-600" />
            ) : (
              <XCircle className="mt-0.5 h-5 w-5 flex-none text-red-600" />
            )}
            <p className="flex-1 text-sm text-slate-700">{t.message}</p>
            <button
              className="text-slate-400 hover:text-slate-600"
              onClick={() => dismiss(t.id)}
              aria-label="Dismiss notification"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
