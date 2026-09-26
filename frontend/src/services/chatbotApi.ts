import type { ApiChatMessage, Message, SendMessagePayload, SendChatResponse } from '../types/chat';
import api from './api';

// ---------------------------------------------------------------------------
// Chat API — the frontend talks only to the Django REST API.
//
// POST /api/chat/ stores the user question and a temporary assistant reply in
// chat_messages, grouped by chat_sessions, and returns both messages together
// with the session id. Sources stay empty until retrieval (RAG) exists.
// ---------------------------------------------------------------------------

/** What the UI needs after a send: the reply and the session it belongs to. */
export interface SendResult {
  sessionId: string;
  message: Message;
}

/** Map an API message (no sources yet) to the UI Message shape. */
function toMessage(raw: ApiChatMessage): Message {
  return {
    id: raw.id,
    role: raw.role,
    content: raw.content,
    sources: [],
    createdAt: raw.created_at,
  };
}

/**
 * Send a question to POST /api/chat/.
 *
 * Pass `sessionId` from a previous call so the backend keeps appending to the
 * same chat_sessions row; omit it to start a new conversation.
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

  return { sessionId: data.session_id, message: toMessage(assistant) };
}

/**
 * Fetch the history of a conversation.
 * TODO: implement once GET /api/chat/<session_id>/ exists.
 */
export async function listMessages(conversationId: string): Promise<Message[]> {
  throw new Error(`listMessages: not implemented yet (conversation: ${conversationId}).`);
}
