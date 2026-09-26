import type { Source } from '../../types/chat';

interface SourceListProps {
  sources: Source[];
}

// Citation block rendered below an assistant answer.
export default function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) return null;

  return (
    <div
      className="mt-3 pt-3"
      style={{ borderTop: '1px solid rgba(192,132,252,0.12)' }}
    >
      <p
        className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-widest"
        style={{ color: '#7c3aed' }}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          className="h-3 w-3"
          aria-hidden="true"
        >
          <path d="M10 13a5 5 0 0 0 7.07 0l2.83-2.83a5 5 0 0 0-7.07-7.07L11.4 4.6" />
          <path d="M14 11a5 5 0 0 0-7.07 0L4.1 13.83a5 5 0 0 0 7.07 7.07L12.6 19.4" />
        </svg>
        Sources
      </p>

      <ol className="space-y-1.5">
        {sources.map((source, index) => (
          <li
            key={`${source.documentId}-${index}`}
            className="flex gap-2 rounded-xl px-3 py-2"
            style={{ background: 'rgba(192,132,252,0.06)', border: '1px solid rgba(192,132,252,0.1)' }}
          >
            <span
              className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
              style={{ background: 'rgba(192,132,252,0.15)', color: '#c084fc' }}
            >
              {index + 1}
            </span>
            <div className="min-w-0 text-xs leading-relaxed">
              <span className="font-medium" style={{ color: '#e8d5f5' }}>{source.documentName}</span>
              {source.pageNumber !== undefined && (
                <span style={{ color: '#6b3fa0' }}> · p. {source.pageNumber}</span>
              )}
              <p className="mt-0.5" style={{ color: '#8b6ab0' }}>{source.excerpt}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
