import { useState } from "react";
import { FileText, ChevronDown, Quote } from "lucide-react";
import type { Citation } from "../types";

export function Citations({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = useState(false);
  if (citations.length === 0) return null;

  return (
    <div className="mt-3 border-t border-slate-200 pt-3">
      <button
        className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-700"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <Quote className="h-3.5 w-3.5" />
        {citations.length} source{citations.length > 1 ? "s" : ""}
        <ChevronDown
          className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <ol className="mt-2 space-y-2">
          {citations.map((c, i) => (
            <li
              key={c.chunk_id}
              className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-xs"
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1 font-medium text-slate-700">
                  <FileText className="h-3.5 w-3.5 text-brand-500" />
                  [{i + 1}] {c.filename}
                </span>
                <span className="rounded-full bg-brand-100 px-2 py-0.5 text-[10px] font-semibold text-brand-700">
                  {(c.similarity * 100).toFixed(0)}% match
                </span>
              </div>
              <p className="leading-relaxed text-slate-600">“{c.snippet}”</p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
