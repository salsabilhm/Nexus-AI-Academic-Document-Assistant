import { useCallback, useState } from 'react';
import type { ChatRole, Message } from '../types/chat';
import { sendMessage } from '../services/chatbotApi';
import { toApiError } from '../services/api';
import { CHAT_DEMO_MODE, createDemoReply } from '../data/demo';

// Local state for a chat conversation.
//
// Two paths:
// - CHAT_DEMO_MODE (current): appends a placeholder reply after a short delay
//   so the loading and citation states can be reviewed without a backend.
// - otherwise: calls chatbotApi.sendMessage() — the real endpoint, which does
//   not exist yet, and surfaces its error honestly.
export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessageToBot = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || isSending) return;

      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user' satisfies ChatRole,
        content: trimmed,
        sources: [],
        createdAt: new Date().toISOString(),
      };

      setMessages((previous) => [...previous, userMessage]);
      setError(null);
      setIsSending(true);

      try {
        if (CHAT_DEMO_MODE) {
          // Simulated latency so the "thinking" state is visible.
          await new Promise((resolve) => setTimeout(resolve, 900));
          setMessages((previous) => [...previous, createDemoReply()]);
          return;
        }

        const reply = await sendMessage({ content: trimmed });
        setMessages((previous) => [...previous, reply]);
      } catch (err) {
        // The chat endpoint does not exist yet: surface the real reason.
        setError(toApiError(err).message);
      } finally {
        setIsSending(false);
      }
    },
    [isSending],
  );

  const clearError = useCallback(() => setError(null), []);

  return { messages, isSending, error, sendMessage: sendMessageToBot, clearError };
}
