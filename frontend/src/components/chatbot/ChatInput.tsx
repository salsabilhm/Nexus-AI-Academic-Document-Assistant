import { useState } from 'react';
import type { FormEvent } from 'react';
import Button from '../common/Button';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

// Question input with a send button. The raw text goes to the parent —
// sending it to the backend is handled by the useChat hook.
export default function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState('');

  const canSend = value.trim().length > 0 && !disabled;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSend) return;
    onSend(value.trim());
    setValue('');
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-slate-200 bg-white p-3 md:p-4">
      <div className="flex items-center gap-2 rounded-2xl border border-slate-300 bg-white px-3 py-2 transition-colors focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-100">
        <input
          type="text"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Ask a question about your documents…"
          disabled={disabled}
          aria-label="Question"
          className="min-w-0 flex-1 bg-transparent px-1 py-1.5 text-sm outline-none placeholder:text-slate-400 disabled:opacity-60"
        />

        <Button type="submit" size="sm" disabled={!canSend} aria-label="Send question">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-4 w-4"
            aria-hidden="true"
          >
            <path d="m4 4 16 8-16 8 3-8-3-8z" />
            <path d="M7 12h13" />
          </svg>
          Send
        </Button>
      </div>

      <p className="mt-2 px-1 text-[11px] text-slate-400">
        Press Enter to send · answers cite the documents they come from
      </p>
    </form>
  );
}
