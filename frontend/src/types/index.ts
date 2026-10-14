// Mirrors the backend Pydantic schemas (app/models/schemas.py).

export interface DocumentMetadata {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  char_count: number;
  chunk_count: number;
  sha256: string;
  uploaded_at: string;
}

export interface DocumentListResponse {
  documents: DocumentMetadata[];
  total: number;
}

export interface UploadResponse {
  document: DocumentMetadata;
  message: string;
}

export interface Citation {
  document_id: string;
  filename: string;
  chunk_id: string;
  chunk_index: number;
  similarity: number;
  snippet: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  grounded: boolean;
  model: string;
  used_fallback: boolean;
}

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  environment: string;
  embedding_backend: string;
  llm_provider: string;
  document_count: number;
}

// Client-side chat message model.
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  grounded?: boolean;
  usedFallback?: boolean;
  model?: string;
  pending?: boolean;
  error?: boolean;
}
