import type { Message, SendMessagePayload } from '../types/chat';

// Chatbot-related API calls.
//
// TODO(chat endpoints): the backend does not expose a chat endpoint yet.
// These placeholders describe the future contract (send a message, receive an
// assistant answer with its sources) without calling any non-existing URL.

export async function sendMessage(payload: SendMessagePayload): Promise<Message> {
  throw new Error(`sendMessage: chat endpoint is not implemented yet (${payload.content}).`);
}

export async function listMessages(conversationId: string): Promise<Message[]> {
  throw new Error(`listMessages: not implemented yet (conversation: ${conversationId}).`);
}
