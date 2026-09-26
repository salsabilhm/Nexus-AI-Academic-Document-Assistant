import type { DocumentItem, DocumentSource, DocumentStatus } from '../../types/document';

interface DocumentCardProps {
  document: DocumentItem;
}

const statusColors: Record<DocumentStatus, { bg: string; color: string; dot: string }> = {
  uploaded: { bg: 'rgba(192,132,252,0.08)', color: '#a78bca', dot: '#a78bca' },
  processing: { bg: 'rgba(251,191,36,0.1)', color: '#d97706', dot: '#f59e0b' },
  ready: { bg: 'rgba(16,185,129,0.1)', color: '#10b981', dot: '#10b981' },
  failed: { bg: 'rgba(239,68,68,0.1)', color: '#ef4444', dot: '#ef4444' },
};

const sourceLabels: Record<DocumentSource, string> = {
  university: 'University',
  student: 'Student',
};

export default function DocumentCard({ document }: DocumentCardProps) {
  const status = statusColors[document.status];

  return (
    <div
      className="flex items-start gap-3 rounded-xl px-3 py-2.5 transition-all"
      style={{
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(192,132,252,0.1)',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(192,132,252,0.22)';
        (e.currentTarget as HTMLDivElement).style.background = 'rgba(192,132,252,0.04)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(192,132,252,0.1)';
        (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.03)';
      }}
    >
      <span
        className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg"
        style={{ background: 'rgba(192,132,252,0.1)', color: '#c084fc' }}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.8}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-3.5 w-3.5"
          aria-hidden="true"
        >
          <path d="M14 3v5h5" />
          <path d="M19 8v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5z" />
          <path d="M9 13h6M9 17h4" />
        </svg>
      </span>

      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-medium" style={{ color: '#e8d5f5' }} title={document.name}>
          {document.name}
        </p>
        <p className="mt-0.5 text-[11px]" style={{ color: '#6b3fa0' }}>
          {sourceLabels[document.source]} ·{' '}
          {new Date(document.createdAt).toLocaleDateString(undefined, {
            day: 'numeric',
            month: 'short',
          })}
        </p>
      </div>

      <span
        className="inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium capitalize"
        style={{ background: status.bg, color: status.color }}
      >
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: status.dot }} />
        {document.status}
      </span>
    </div>
  );
}
