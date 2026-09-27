import type { ApiChatMessage, ApiSource, Message, SendMessagePayload, SendChatResponse, Source } from '../types/chat';
import api from './api';

// ---------------------------------------------------------------------------
// Chat API — the frontend talks only to the Django REST API.
//
// POST /api/chat/ runs the Nexus agent (history -> RAG -> Gemini), stores both
// turns in chat_messages grouped by chat_sessions, and returns them together
// with the session id, the grounded answer and the sources the agent actually
// retrieved (never fabricated).
// ---------------------------------------------------------------------------

/** What the UI needs after a send: the reply and the session it belongs to. */
export interface SendResult {
  sessionId: string;
  message: Message;
}

/** Map an API message to the UI Message shape. */
function toMessage(raw: ApiChatMessage, sources: Source[] = []): Message {
  return {
    id: raw.id,
    role: raw.role,
    content: raw.content,
    sources,
    createdAt: raw.created_at,
  };
}

/** Map an API source to the UI Source shape (only real fields). */
function toSources(apiSources: ApiSource[]): Source[] {
  return apiSources.map((source) => ({
    documentId: source.document_id,
    documentName: source.document_name,
    documentType: source.document_type,
    section: source.section ?? undefined,
    excerpt: source.excerpt,
    pageNumber: source.page ?? undefined,
  }));
}

/**
 * Send a question to POST /api/chat/.
 *
 * Pass `sessionId` from a previous call so the backend keeps appending to the
 * same chat_sessions row; omit it to start a new conversation. The grounded
 * sources returned by the agent are attached to the assistant message so the
 * citation block renders them.
 */
export async function sendMessage(payload: SendMessagePayload): Promise<SendResult> {
  const { data } = await api.post<SendChatResponse>('/chat/', {
    question: payload.content,
    session_id: payload.sessionId ?? null,
  });

  const assistant = [...data.messages].reverse().find((m) => m.role === 'assistant');
  if (!assistant) {
    throw new Error('sendMessage: the API response contained no assistant message.');
  }

  return {
    sessionId: data.session_id,
    message: toMessage(assistant, toSources(data.sources ?? [])),
  };
}

/**
 * Fetch the history of a conversation.
 * TODO: implement once GET /api/chat/<session_id>/ exists.
 */
export async function listMessages(conversationId: string): Promise<Message[]> {
  throw new Error(`listMessages: not implemented yet (conversation: ${conversationId}).`);
}
