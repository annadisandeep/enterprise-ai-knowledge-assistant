import { useEffect, useRef, useState } from "react";
import { SendHorizontal, Sparkles, MessageSquare } from "lucide-react";
import { ApiError, askQuestion } from "../lib/api";
import { uid } from "../lib/utils";
import type { ChatMessage as Msg } from "../types";
import { ChatMessage } from "./ChatMessage";
import { EmptyState } from "./EmptyState";

const SUGGESTIONS = [
  "Summarise the key points across my documents.",
  "What does the policy say about remote work?",
  "List the main security requirements.",
];

export function ChatPanel({ hasDocuments }: { hasDocuments: boolean }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const send = async (question: string) => {
    const text = question.trim();
    if (!text || sending) return;
    setInput("");
    const userMsg: Msg = { id: uid("u"), role: "user", content: text };
    const pendingId = uid("a");
    setMessages((m) => [
      ...m,
      userMsg,
      { id: pendingId, role: "assistant", content: "", pending: true },
    ]);
    setSending(true);
    try {
      const res = await askQuestion(text);
      setMessages((m) =>
        m.map((msg) =>
          msg.id === pendingId
            ? {
                id: pendingId,
                role: "assistant",
                content: res.answer,
                citations: res.citations,
                grounded: res.grounded,
                usedFallback: res.used_fallback,
                model: res.model,
              }
            : msg,
        ),
      );
    } catch (err) {
      const detail = err instanceof ApiError ? err.message : "Something went wrong.";
      setMessages((m) =>
        m.map((msg) =>
          msg.id === pendingId
            ? { id: pendingId, role: "assistant", content: detail, error: true }
            : msg,
        ),
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        {messages.length === 0 ? (
          <div className="mx-auto max-w-2xl">
            <EmptyState
              icon={<MessageSquare className="h-6 w-6" />}
              title="Ask your knowledge base"
              description={
                hasDocuments
                  ? "Ask a question and get an answer grounded in your uploaded documents, with citations."
                  : "Upload documents first, then ask questions. Answers are grounded only in what you provide."
              }
            />
            {hasDocuments && (
              <div className="mt-6">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Try asking
                </p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 transition hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700"
                      onClick={() => send(s)}
                    >
                      <Sparkles className="h-3 w-3 text-brand-500" />
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-5">
            {messages.map((m) => (
              <ChatMessage key={m.id} message={m} />
            ))}
          </div>
        )}
      </div>

      <form
        className="border-t border-slate-200 bg-white px-4 py-3 sm:px-6"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <div className="mx-auto flex max-w-2xl items-end gap-2">
          <label htmlFor="chat-input" className="sr-only">
            Ask a question
          </label>
          <textarea
            id="chat-input"
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            placeholder="Ask a question about your documents…"
            className="max-h-40 flex-1 resize-none rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <button
            type="submit"
            className="btn-primary h-[42px]"
            disabled={sending || !input.trim()}
            aria-label="Send question"
          >
            <SendHorizontal className="h-4 w-4" />
          </button>
        </div>
        <p className="mx-auto mt-1.5 max-w-2xl text-[11px] text-slate-400">
          Answers are generated from your documents. Verify important information.
        </p>
      </form>
    </div>
  );
}
