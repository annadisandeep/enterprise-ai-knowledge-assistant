import { MessagesSquare, Library, BrainCircuit, X, Circle } from "lucide-react";
import type { HealthResponse } from "../types";

export type View = "chat" | "documents";

const NAV: { id: View; label: string; icon: typeof MessagesSquare }[] = [
  { id: "chat", label: "Chat", icon: MessagesSquare },
  { id: "documents", label: "Documents", icon: Library },
];

export function Sidebar({
  active,
  onNavigate,
  documentCount,
  health,
  mobileOpen,
  onCloseMobile,
}: {
  active: View;
  onNavigate: (v: View) => void;
  documentCount: number;
  health: HealthResponse | null;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}) {
  const content = (
    <div className="flex h-full w-64 flex-col bg-slate-900 text-slate-300">
      <div className="flex items-center justify-between px-5 py-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
            <BrainCircuit className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-white">Knowledge</p>
            <p className="text-xs text-slate-400">Assistant</p>
          </div>
        </div>
        <button
          className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
          onClick={onCloseMobile}
          aria-label="Close menu"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-1 px-3" aria-label="Primary">
        {NAV.map(({ id, label, icon: Icon }) => {
          const isActive = active === id;
          return (
            <button
              key={id}
              onClick={() => {
                onNavigate(id);
                onCloseMobile();
              }}
              aria-current={isActive ? "page" : undefined}
              className={`flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? "bg-brand-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <span className="flex items-center gap-3">
                <Icon className="h-4 w-4" />
                {label}
              </span>
              {id === "documents" && documentCount > 0 && (
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                    isActive ? "bg-white/20 text-white" : "bg-slate-700 text-slate-200"
                  }`}
                >
                  {documentCount}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="border-t border-slate-800 px-5 py-4 text-xs">
        <div className="flex items-center gap-2">
          <Circle
            className={`h-2.5 w-2.5 ${
              health ? "fill-green-500 text-green-500" : "fill-slate-500 text-slate-500"
            }`}
          />
          <span className="text-slate-400">
            {health ? `Online · ${health.environment}` : "Connecting…"}
          </span>
        </div>
        {health && (
          <p className="mt-1.5 text-[11px] text-slate-500">
            {health.llm_provider} · {health.embedding_backend.split("/").pop()}
          </p>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop */}
      <aside className="hidden lg:block">{content}</aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-slate-900/50"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          <div className="absolute left-0 top-0 h-full animate-fade-in">{content}</div>
        </div>
      )}
    </>
  );
}
