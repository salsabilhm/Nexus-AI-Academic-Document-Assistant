import { useCallback, useState } from 'react';
import type { ChatRole, Message } from '../types/chat';
import { sendMessage } from '../services/chatbotApi';
import { toApiError } from '../services/api';
import { CHAT_DEMO_MODE, createDemoReply } from '../data/demo';

// Local state for a chat conversation.
//
// The session id lives in the page (Chatbot) because the document sidebar
// needs it too: uploads and questions must land in the same chat_sessions row.
//
// Two paths:
// - CHAT_DEMO_MODE (off): appends a placeholder reply after a short delay so
//   the loading and citation states can be reviewed without a backend.
// - otherwise (current): POSTs the question to /api/chat/ and appends the
//   assistant reply the backend saved. The session id returned by the API is
//   handed back through `onSessionId` so every follow-up question lands in the
//   same chat_sessions row.
export function useChat(
  sessionId: string | null,
  onSessionId: (id: string) => void,
) {
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

        const result = await sendMessage({
          content: trimmed,
          sessionId: sessionId ?? undefined,
        });
        // Remember the session so the next question groups with this one.
        onSessionId(result.sessionId);
        setMessages((previous) => [...previous, result.message]);
      } catch (err) {
        // Surface the real reason the API rejected or failed the request.
        setError(toApiError(err).message);
      } finally {
        setIsSending(false);
      }
    },
    [isSending, sessionId, onSessionId],
  );

  const clearError = useCallback(() => setError(null), []);

  /** Drop the conversation shown on screen ("New session"). */
  const resetChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setIsSending(false);
  }, []);

  return {
    messages,
    isSending,
    error,
    sendMessage: sendMessageToBot,
    clearError,
    resetChat,
  };
}
