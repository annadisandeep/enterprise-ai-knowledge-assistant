import { useState } from "react";
import { FileText, Trash2, Hash, Database } from "lucide-react";
import type { DocumentMetadata } from "../types";
import { formatBytes, formatDate } from "../lib/utils";
import { ConfirmDialog } from "./ConfirmDialog";
import { EmptyState } from "./EmptyState";
import { LoadingRow } from "./Spinner";

export function DocumentLibrary({
  documents,
  loading,
  onDelete,
}: {
  documents: DocumentMetadata[];
  loading: boolean;
  onDelete: (doc: DocumentMetadata) => Promise<void>;
}) {
  const [pending, setPending] = useState<DocumentMetadata | null>(null);
  const [deleting, setDeleting] = useState(false);

  const confirmDelete = async () => {
    if (!pending) return;
    setDeleting(true);
    try {
      await onDelete(pending);
      setPending(null);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="card p-6">
        <LoadingRow label="Loading documents…" />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <EmptyState
        icon={<Database className="h-6 w-6" />}
        title="No documents yet"
        description="Upload a PDF, text, or Markdown file to build your knowledge base. Then ask questions in the chat."
      />
    );
  }

  return (
    <>
      <ul className="space-y-2" aria-label="Document library">
        {documents.map((doc) => (
          <li
            key={doc.id}
            className="card flex items-center gap-3 p-3 transition hover:shadow-md"
          >
            <div className="flex h-10 w-10 flex-none items-center justify-center rounded-lg bg-brand-50 text-brand-600">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-800">
                {doc.filename}
              </p>
              <p className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-slate-500">
                <span>{formatBytes(doc.size_bytes)}</span>
                <span className="inline-flex items-center gap-1">
                  <Hash className="h-3 w-3" />
                  {doc.chunk_count} chunks
                </span>
                <span>{formatDate(doc.uploaded_at)}</span>
              </p>
            </div>
            <button
              className="btn-ghost text-slate-400 hover:text-red-600"
              onClick={() => setPending(doc)}
              aria-label={`Delete ${doc.filename}`}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </li>
        ))}
      </ul>

      <ConfirmDialog
        open={pending !== null}
        title="Delete document?"
        message={`"${pending?.filename}" and its ${pending?.chunk_count ?? 0} indexed chunks will be permanently removed. This cannot be undone.`}
        confirmLabel={deleting ? "Deleting…" : "Delete"}
        busy={deleting}
        onConfirm={confirmDelete}
        onCancel={() => setPending(null)}
      />
    </>
  );
}
