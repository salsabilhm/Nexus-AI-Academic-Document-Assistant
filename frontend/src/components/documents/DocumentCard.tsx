import type { DocumentItem, DocumentStatus, DocumentType } from '../../types/document';

interface DocumentCardProps {
  document: DocumentItem;
}

const typeLabels: Record<DocumentType, string> = {
  requirement: 'Requirement',
  guideline: 'Guideline',
  template: 'Template',
  research: 'Research',
  thesis: 'Thesis',
};

const statusStyles: Record<DocumentStatus, string> = {
  uploaded: 'bg-slate-100 text-slate-600',
  processing: 'bg-amber-100 text-amber-700',
  ready: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-red-100 text-red-700',
};

// Compact summary of a single document: icon, name, metadata and status.
export default function DocumentCard({ document }: DocumentCardProps) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5 transition-colors hover:border-slate-300">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-4 w-4"
          aria-hidden="true"
        >
          <path d="M14 3v5h5" />
          <path d="M19 8v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5z" />
          <path d="M9 13h6M9 17h4" />
        </svg>
      </span>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-800" title={document.name}>
          {document.name}
        </p>
        <p className="mt-0.5 text-xs text-slate-500">
          {typeLabels[document.type]} · added{' '}
          {new Date(document.createdAt).toLocaleDateString(undefined, {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
          })}
        </p>
      </div>

      <span className={`pill shrink-0 capitalize ${statusStyles[document.status]}`}>
        {document.status}
      </span>
    </div>
  );
}
