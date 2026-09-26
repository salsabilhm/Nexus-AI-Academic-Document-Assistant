// Types describing chatbot conversations and the sources used for an answer.

export type ChatRole = 'user' | 'assistant';

/** A passage taken from an uploaded document that supported an answer. */
export interface Source {
  documentId: string;
  documentName: string;
  excerpt: string;
  pageNumber?: number;
}

export interface Message {
  id: string;
  role: ChatRole;
  content: string;
  sources: Source[];
  createdAt: string;
}

/** Payload sent to POST /api/chat/. */
export interface SendMessagePayload {
  /** chat_sessions id to continue; omit to start a new session. */
  sessionId?: string;
  content: string;
}

/** One message as returned by the API (Django/DRF snake_case). */
export interface ApiChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  created_at: string;
}

/** Response body of POST /api/chat/. */
export interface SendChatResponse {
  session_id: string;
  session_title: string;
  messages: ApiChatMessage[];
}
