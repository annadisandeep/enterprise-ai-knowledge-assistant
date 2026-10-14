import { Loader2 } from "lucide-react";

export function Spinner({ className = "" }: { className?: string }) {
  return <Loader2 className={`animate-spin ${className}`} aria-hidden="true" />;
}

export function LoadingRow({ label }: { label: string }) {
  return (
    <div
      className="flex items-center gap-2 text-sm text-slate-500"
      role="status"
      aria-live="polite"
    >
      <Spinner className="h-4 w-4" />
      <span>{label}</span>
    </div>
  );
}
