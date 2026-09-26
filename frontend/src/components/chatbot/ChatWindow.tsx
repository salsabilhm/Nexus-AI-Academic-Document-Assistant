import { useEffect, useRef } from 'react';
import type { Message } from '../../types/chat';
import ChatMessage from './ChatMessage';
import Loading from '../common/Loading';
import NexusLogo from '../common/NexusLogo';

interface ChatWindowProps {
  messages: Message[];
  isSending?: boolean;
  suggestions?: string[];
  onSelectSuggestion?: (text: string) => void;
}

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
        <div className="max-w-sm text-center">
          {/* Logo */}
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl" style={{ background: 'rgba(192,132,252,0.1)', border: '1px solid rgba(192,132,252,0.15)' }}>
            <NexusLogo size={40} />
          </div>

          <h2 className="mb-2 text-lg font-semibold" style={{ color: '#f0e4ff' }}>
            Hi, I'm Nexus
          </h2>
          <p className="mb-1 text-sm" style={{ color: '#a78bca' }}>
            Your AI academic document assistant.
          </p>
          <p className="text-sm leading-relaxed" style={{ color: '#6b3fa0' }}>
            Upload your papers or ask a question about your research requirements.
          </p>

          {suggestions.length > 0 && (
            <div className="mt-7">
              <p
                className="mb-3 text-[10px] font-semibold uppercase tracking-widest"
                style={{ color: '#6b3fa0' }}
              >
                Try asking
              </p>
              <div className="flex flex-col gap-2">
                {suggestions.map((text) => (
                  <button
                    key={text}
                    type="button"
                    onClick={() => onSelectSuggestion?.(text)}
                    className="rounded-xl px-4 py-2.5 text-left text-sm transition-all"
                    style={{
                      background: 'rgba(255,255,255,0.03)',
                      border: '1px solid rgba(192,132,252,0.14)',
                      color: '#c4a8e0',
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(192,132,252,0.35)';
                      (e.currentTarget as HTMLButtonElement).style.background = 'rgba(192,132,252,0.07)';
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(192,132,252,0.14)';
                      (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.03)';
                    }}
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
      <div className="flex flex-col gap-5 p-5 md:p-6">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isSending && (
          <div className="flex justify-start gap-3">
            <NexusLogo size={28} className="mt-1 flex-shrink-0" />
            <div
              className="rounded-2xl rounded-bl-md px-5 py-4"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(192,132,252,0.12)' }}
            >
              <Loading label="Nexus is thinking…" />
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>
    </div>
  );
}
