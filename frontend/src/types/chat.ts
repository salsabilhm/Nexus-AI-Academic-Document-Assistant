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

/** Payload sent to the future chat endpoint. */
export interface SendMessagePayload {
  conversationId?: string;
  content: string;
}
