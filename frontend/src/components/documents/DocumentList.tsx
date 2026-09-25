import type { DocumentItem } from '../../types/document';
import DocumentCard from './DocumentCard';

interface DocumentListProps {
  documents: DocumentItem[];
}

// Renders the document collection with a clear empty state.
export default function DocumentList({ documents }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center">
        <p className="text-sm font-medium text-slate-600">No documents yet</p>
        <p className="mt-1 text-xs text-slate-500">
          Upload your first university document to get started.
        </p>
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-2">
      {documents.map((document) => (
        <li key={document.id}>
          <DocumentCard document={document} />
        </li>
      ))}
    </ul>
  );
}
