import type { Source } from '../../types/chat';

interface SourceListProps {
  sources: Source[];
}

// Citation block rendered below an assistant answer.
// Retrieval happens on the backend — this component only displays what the
// API returns, so the UI never talks to documents or the vector store itself.
export default function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) return null;

  return (
    <div className="mt-3 border-t border-slate-100 pt-3">
      <p className="section-label flex items-center gap-1.5">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          className="h-3.5 w-3.5"
          aria-hidden="true"
        >
          <path d="M10 13a5 5 0 0 0 7.07 0l2.83-2.83a5 5 0 0 0-7.07-7.07L11.4 4.6" />
          <path d="M14 11a5 5 0 0 0-7.07 0L4.1 13.83a5 5 0 0 0 7.07 7.07L12.6 19.4" />
        </svg>
        Sources
      </p>

      <ol className="mt-2 space-y-1.5">
        {sources.map((source, index) => (
          <li
            key={`${source.documentId}-${index}`}
            className="flex gap-2 rounded-lg bg-slate-50 px-2.5 py-2"
          >
            <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-[10px] font-semibold text-indigo-700">
              {index + 1}
            </span>
            <div className="min-w-0 text-xs leading-relaxed">
              <span className="font-medium text-slate-700">{source.documentName}</span>
              {source.pageNumber !== undefined && (
                <span className="text-slate-400"> · p. {source.pageNumber}</span>
              )}
              <p className="mt-0.5 text-slate-500">{source.excerpt}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
