import { useCallback, useEffect, useState } from "react";
import { Menu, UploadCloud } from "lucide-react";
import { Sidebar, type View } from "./components/Sidebar";
import { ChatPanel } from "./components/ChatPanel";
import { DocumentLibrary } from "./components/DocumentLibrary";
import { UploadDropzone } from "./components/UploadDropzone";
import { ToastProvider, useToast } from "./components/Toast";
import {
  ApiError,
  deleteDocument,
  getHealth,
  listDocuments,
} from "./lib/api";
import type { DocumentMetadata, HealthResponse } from "./types";

function AppShell() {
  const { notify } = useToast();
  const [view, setView] = useState<View>("chat");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const refreshDocuments = useCallback(async () => {
    try {
      const res = await listDocuments();
      setDocuments(res.documents);
    } catch (err) {
      const detail = err instanceof ApiError ? err.message : "Could not load documents.";
      notify("error", detail);
    } finally {
      setLoadingDocs(false);
    }
  }, [notify]);

  const refreshHealth = useCallback(async () => {
    try {
      setHealth(await getHealth());
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    refreshHealth();
    refreshDocuments();
  }, [refreshHealth, refreshDocuments]);

  const handleDelete = useCallback(
    async (doc: DocumentMetadata) => {
      try {
        await deleteDocument(doc.id);
        notify("success", `Deleted "${doc.filename}".`);
        await Promise.all([refreshDocuments(), refreshHealth()]);
      } catch (err) {
        const detail = err instanceof ApiError ? err.message : "Delete failed.";
        notify("error", detail);
      }
    },
    [notify, refreshDocuments, refreshHealth],
  );

  const handleUploaded = useCallback(() => {
    refreshDocuments();
    refreshHealth();
  }, [refreshDocuments, refreshHealth]);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        active={view}
        onNavigate={setView}
        documentCount={documents.length}
        health={health}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3 sm:px-6">
          <button
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <h1 className="text-base font-semibold text-slate-800">
            {view === "chat" ? "Chat" : "Document Library"}
          </h1>
          <div className="ml-auto flex items-center gap-2">
            {view === "documents" && (
              <span className="text-sm text-slate-500">
                {documents.length} document{documents.length === 1 ? "" : "s"}
              </span>
            )}
            {view === "chat" && (
              <button className="btn-ghost text-sm" onClick={() => setView("documents")}>
                <UploadCloud className="h-4 w-4" /> Manage documents
              </button>
            )}
          </div>
        </header>

        <main className="min-h-0 flex-1 overflow-hidden bg-slate-50">
          {view === "chat" ? (
            <ChatPanel hasDocuments={documents.length > 0} />
          ) : (
            <div className="h-full overflow-y-auto px-4 py-6 sm:px-6">
              <div className="mx-auto max-w-3xl space-y-6">
                <section>
                  <h2 className="mb-3 text-sm font-semibold text-slate-700">
                    Upload documents
                  </h2>
                  <UploadDropzone onUploaded={handleUploaded} />
                </section>
                <section>
                  <h2 className="mb-3 text-sm font-semibold text-slate-700">
                    Your documents
                  </h2>
                  <DocumentLibrary
                    documents={documents}
                    loading={loadingDocs}
                    onDelete={handleDelete}
                  />
                </section>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppShell />
    </ToastProvider>
  );
}
