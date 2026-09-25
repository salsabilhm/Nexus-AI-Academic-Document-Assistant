import type { Message } from '../../types/chat';
import SourceList from './SourceList';

interface ChatMessageProps {
  message: Message;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

// A single conversation turn: user bubble on the right, assistant card (with
// its citations) on the left.
export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-indigo-600 px-4 py-2.5 text-sm text-white md:max-w-[70%]">
          <p className="whitespace-pre-wrap">{message.content}</p>
          <p className="mt-1 text-[10px] text-indigo-200">{formatTime(message.createdAt)}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start gap-2.5">
      <span
        className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 text-xs font-bold text-white"
        aria-hidden="true"
      >
        N
      </span>

      <div className="max-w-[85%] md:max-w-[75%]">
        <div className="card px-4 py-3">
          <p className="mb-1.5 text-xs font-semibold text-slate-500">Nexus</p>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
            {message.content}
          </p>
          <SourceList sources={message.sources} />
        </div>
        <p className="mt-1 pl-1 text-[10px] text-slate-400">{formatTime(message.createdAt)}</p>
      </div>
    </div>
  );
}
