import { useCallback, useRef, useState } from "react";
import { UploadCloud, FileText, CheckCircle2, XCircle } from "lucide-react";
import { ApiError, uploadDocument } from "../lib/api";
import { fileExtension, formatBytes } from "../lib/utils";
import { Spinner } from "./Spinner";

const ALLOWED = [".pdf", ".txt", ".md", ".markdown"];
const MAX_BYTES = 10 * 1024 * 1024;

type Status = "processing" | "done" | "error";
interface UploadItem {
  name: string;
  size: number;
  status: Status;
  detail?: string;
}

export function UploadDropzone({ onUploaded }: { onUploaded: () => void }) {
  const [dragging, setDragging] = useState(false);
  const [items, setItems] = useState<UploadItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const update = useCallback((name: string, patch: Partial<UploadItem>) => {
    setItems((prev) =>
      prev.map((it) => (it.name === name ? { ...it, ...patch } : it)),
    );
  }, []);

  const handleFiles = useCallback(
    async (fileList: FileList | File[]) => {
      const files = Array.from(fileList);
      for (const file of files) {
        const ext = fileExtension(file.name);
        if (!ALLOWED.includes(ext)) {
          setItems((p) => [
            ...p.filter((i) => i.name !== file.name),
            { name: file.name, size: file.size, status: "error", detail: `Unsupported type ${ext || "(none)"}` },
          ]);
          continue;
        }
        if (file.size > MAX_BYTES) {
          setItems((p) => [
            ...p.filter((i) => i.name !== file.name),
            { name: file.name, size: file.size, status: "error", detail: "File exceeds 10 MB" },
          ]);
          continue;
        }
        setItems((p) => [
          ...p.filter((i) => i.name !== file.name),
          { name: file.name, size: file.size, status: "processing" },
        ]);
        try {
          await uploadDocument(file);
          update(file.name, { status: "done", detail: "Indexed" });
          onUploaded();
        } catch (err) {
          const detail = err instanceof ApiError ? err.message : "Upload failed";
          update(file.name, { status: "error", detail });
        }
      }
    },
    [onUploaded, update],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (e.dataTransfer.files?.length) handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload documents. Drag and drop files here or activate to browse."
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
          dragging
            ? "border-brand-500 bg-brand-50"
            : "border-slate-300 bg-white hover:border-brand-400 hover:bg-slate-50"
        }`}
      >
        <UploadCloud className="mb-2 h-8 w-8 text-brand-500" />
        <p className="text-sm font-medium text-slate-700">
          Drag &amp; drop files, or <span className="text-brand-600">browse</span>
        </p>
        <p className="mt-1 text-xs text-slate-500">PDF, TXT, or Markdown · up to 10 MB</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ALLOWED.join(",")}
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.length) handleFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {items.length > 0 && (
        <ul className="mt-4 space-y-2">
          {items.map((it) => (
            <li
              key={it.name}
              className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2"
            >
              <FileText className="h-4 w-4 flex-none text-slate-400" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-700">{it.name}</p>
                <p className="text-xs text-slate-500">
                  {formatBytes(it.size)}
                  {it.detail ? ` · ${it.detail}` : ""}
                </p>
              </div>
              {it.status === "processing" && <Spinner className="h-4 w-4 text-brand-500" />}
              {it.status === "done" && <CheckCircle2 className="h-4 w-4 text-green-600" />}
              {it.status === "error" && <XCircle className="h-4 w-4 text-red-600" />}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
