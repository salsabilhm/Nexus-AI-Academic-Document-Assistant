import type { Message } from '../../types/chat';
import SourceList from './SourceList';
import NexusLogo from '../common/NexusLogo';

interface ChatMessageProps {
  message: Message;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div
          className="max-w-[80%] rounded-2xl rounded-br-md px-4 py-3 text-sm md:max-w-[65%]"
          style={{
            background: 'rgba(192,132,252,0.16)',
            border: '1px solid rgba(192,132,252,0.22)',
            color: '#e8d5f5',
          }}
        >
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          <p className="mt-1.5 text-right text-[10px]" style={{ color: 'rgba(192,132,252,0.5)' }}>
            {formatTime(message.createdAt)}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start gap-3">
      <NexusLogo size={28} className="mt-1 flex-shrink-0" />

      <div className="max-w-[85%] md:max-w-[75%]">
        <div
          className="rounded-2xl rounded-bl-md px-4 py-3"
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(192,132,252,0.12)',
          }}
        >
          <p
            className="mb-1.5 text-[11px] font-semibold uppercase tracking-widest"
            style={{ color: '#7c3aed' }}
          >
            Nexus
          </p>
          <p
            className="whitespace-pre-wrap text-sm leading-relaxed"
            style={{ color: '#e8d5f5' }}
          >
            {message.content}
          </p>
          <SourceList sources={message.sources} />
        </div>
        <p className="mt-1 pl-1 text-[10px]" style={{ color: 'rgba(192,132,252,0.35)' }}>
          {formatTime(message.createdAt)}
        </p>
      </div>
    </div>
  );
}
