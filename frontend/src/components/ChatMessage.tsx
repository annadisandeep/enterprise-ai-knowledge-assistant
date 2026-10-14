import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import { Bot, User, AlertCircle, ShieldCheck } from "lucide-react";
import type { ChatMessage as Msg } from "../types";
import { Citations } from "./Citations";
import { Spinner } from "./Spinner";

export function ChatMessage({ message }: { message: Msg }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 flex-none items-center justify-center rounded-full ${
          isUser ? "bg-slate-700 text-white" : "bg-brand-600 text-white"
        }`}
        aria-hidden="true"
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className={`min-w-0 max-w-[80%] ${isUser ? "text-right" : ""}`}>
        <div
          className={`inline-block rounded-2xl px-4 py-2.5 text-left text-sm ${
            isUser
              ? "bg-slate-700 text-white"
              : message.error
                ? "border border-red-200 bg-red-50 text-red-800"
                : "card text-slate-800"
          }`}
        >
          {message.pending ? (
            <span className="flex items-center gap-2 text-slate-500">
              <Spinner className="h-4 w-4" /> Thinking…
            </span>
          ) : isUser ? (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : (
            <div className="prose-chat break-words">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeSanitize]}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {!isUser && !message.pending && !message.error && (
            <>
              {message.usedFallback ? (
                <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700">
                  <AlertCircle className="h-3 w-3" /> No grounded answer found
                </div>
              ) : message.grounded ? (
                <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-[11px] font-medium text-green-700">
                  <ShieldCheck className="h-3 w-3" /> Grounded in your documents
                </div>
              ) : null}
              {message.citations && <Citations citations={message.citations} />}
            </>
          )}
        </div>
        {message.model && !message.pending && !isUser && (
          <p className="mt-1 text-[11px] text-slate-400">{message.model}</p>
        )}
      </div>
    </div>
  );
}
