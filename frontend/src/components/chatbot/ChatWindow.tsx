import { useEffect, useRef } from 'react';
import type { Message } from '../../types/chat';
import ChatMessage from './ChatMessage';
import Loading from '../common/Loading';

interface ChatWindowProps {
  messages: Message[];
  isSending?: boolean;
  /** Starter questions shown in the empty state. */
  suggestions?: string[];
  onSelectSuggestion?: (text: string) => void;
}

// Scrollable conversation area with an empty state that explains how to start.
// Pure presentation: no API calls happen here.
export default function ChatWindow({
  messages,
  isSending = false,
  suggestions = [],
  onSelectSuggestion,
}: ChatWindowProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  if (messages.length === 0 && !isSending) {
    return (
      <div className="flex h-full items-center justify-center overflow-y-auto p-6">
        <div className="max-w-md text-center">
          <span className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-6 w-6"
              aria-hidden="true"
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              <path d="M8 9h8M8 13h5" />
            </svg>
          </span>

          <h2 className="text-lg font-semibold text-slate-900">Ask Nexus about your documents</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            Upload university requirements and your research, then ask a question in plain
            language. Every answer comes with the sources it was built from.
          </p>

          {suggestions.length > 0 && (
            <div className="mt-5">
              <p className="section-label mb-2">Try one of these</p>
              <div className="flex flex-col gap-2">
                {suggestions.map((text) => (
                  <button
                    key={text}
                    type="button"
                    onClick={() => onSelectSuggestion?.(text)}
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-xs text-slate-600 transition-colors hover:border-indigo-300 hover:bg-indigo-50/50 hover:text-slate-900"
                  >
                    {text}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="flex flex-col gap-4 p-4 md:p-6">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isSending && (
          <div className="flex justify-start gap-2.5">
            <span
              className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 text-xs font-bold text-white"
              aria-hidden="true"
            >
              N
            </span>
            <div className="card flex items-center px-4 py-3">
              <Loading label="Nexus is thinking…" />
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>
    </div>
  );
}
