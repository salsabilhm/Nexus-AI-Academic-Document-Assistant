import { useState } from 'react';
import type { FormEvent } from 'react';

interface ChatInputProps {
  onSend: (content: string) => void;
  onNewSession?: () => void;
  disabled?: boolean;
}

export default function ChatInput({
  onSend,
  onNewSession,
  disabled = false,
}: ChatInputProps) {
  const [value, setValue] = useState('');

  const canSend = value.trim().length > 0 && !disabled;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSend) return;
    onSend(value.trim());
    setValue('');
  };

  return (
    <div
      className="px-4 pb-4 pt-3 md:px-5"
      style={{ borderTop: '1px solid rgba(192,132,252,0.1)' }}
    >
      <form onSubmit={handleSubmit}>
        <div
          className="flex items-center gap-2 rounded-2xl px-3 py-2 transition-all"
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(192,132,252,0.2)',
          }}
          onFocusCapture={(e) => {
            (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(192,132,252,0.5)';
            (e.currentTarget as HTMLDivElement).style.boxShadow = '0 0 0 3px rgba(192,132,252,0.08)';
          }}
          onBlurCapture={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget)) {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(192,132,252,0.2)';
              (e.currentTarget as HTMLDivElement).style.boxShadow = 'none';
            }
          }}
        >
          <input
            type="text"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder="Ask Nexus…"
            disabled={disabled}
            aria-label="Ask Nexus"
            className="min-w-0 flex-1 bg-transparent px-2 py-1.5 text-sm outline-none disabled:opacity-60"
            style={{ color: '#e8d5f5' }}
          />

          {/* Send button */}
          <button
            type="submit"
            disabled={!canSend}
            aria-label="Send message"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl transition-all disabled:opacity-30"
            style={{
              background: canSend ? 'linear-gradient(135deg, #c084fc, #7c3aed)' : 'rgba(192,132,252,0.1)',
              color: canSend ? '#0d0014' : '#6b3fa0',
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
              <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
          </button>
        </div>
      </form>

      {/* Bottom action bar */}
      <div className="mt-2 flex items-center justify-between px-1">
        <p className="text-[11px]" style={{ color: 'rgba(192,132,252,0.35)' }}>
          Enter to send · answers cite your documents
        </p>

        {/* New Session */}
        <button
          type="button"
          onClick={onNewSession}
          disabled={disabled}
          className="flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-medium transition-all disabled:opacity-50"
          style={{ color: '#7c3aed', border: '1px solid rgba(192,132,252,0.15)' }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(192,132,252,0.35)';
            (e.currentTarget as HTMLButtonElement).style.color = '#c084fc';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(192,132,252,0.15)';
            (e.currentTarget as HTMLButtonElement).style.color = '#7c3aed';
          }}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3" aria-hidden="true">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
            <path d="M3 3v5h5" />
          </svg>
          New session
        </button>
      </div>
    </div>
  );
}
