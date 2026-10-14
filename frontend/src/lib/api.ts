// Thin, typed API client for the backend. Centralises base URL, the optional
// API key header, and error normalisation so components get clean messages.

import type {
  ChatResponse,
  DocumentListResponse,
  HealthResponse,
  UploadResponse,
} from "../types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || "/api";

// SECURITY: VITE_* values are inlined into the public bundle at build time, so
// this key is readable by anyone who loads the site. Only ever set VITE_API_KEY
// for local dev or a trusted/internal deployment — never a privileged production
// backend key, and never the Gemini key (which is backend-only). See
// frontend/.env.example and docs/SECURITY.md.
const API_KEY = (import.meta.env.VITE_API_KEY as string) || "";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function authHeaders(): Record<string, string> {
  return API_KEY ? { "X-API-Key": API_KEY } : {};
}

async function parseError(res: Response): Promise<never> {
  let detail = `Request failed (${res.status})`;
  try {
    const body = await res.json();
    if (body && typeof body.detail === "string") detail = body.detail;
  } catch {
    // non-JSON error body; keep the default message
  }
  throw new ApiError(detail, res.status);
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/health`, { headers: authHeaders() });
  if (!res.ok) return parseError(res);
  return res.json();
}

export async function listDocuments(): Promise<DocumentListResponse> {
  const res = await fetch(`${BASE_URL}/documents`, { headers: authHeaders() });
  if (!res.ok) return parseError(res);
  return res.json();
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE_URL}/documents`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) return parseError(res);
  return res.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/documents/${encodeURIComponent(id)}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) return parseError(res);
}

export async function askQuestion(
  question: string,
  options: { topK?: number; documentId?: string } = {},
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      question,
      top_k: options.topK,
      document_id: options.documentId,
    }),
  });
  if (!res.ok) return parseError(res);
  return res.json();
}
