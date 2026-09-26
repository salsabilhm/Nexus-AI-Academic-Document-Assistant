import type { DocumentItem } from '../../types/document';
import DocumentCard from './DocumentCard';

interface DocumentListProps {
  documents: DocumentItem[];
}

// Renders the documents of the chat session that is currently open — the
// caller never passes files from another session, so an empty list simply
// means "nothing uploaded here yet".
export default function DocumentList({ documents }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div
        className="rounded-xl border border-dashed px-4 py-6 text-center"
        style={{ borderColor: 'rgba(192,132,252,0.15)', background: 'rgba(255,255,255,0.02)' }}
      >
        <p className="text-xs font-medium" style={{ color: '#a78bca' }}>No documents in this session</p>
        <p className="mt-1 text-[11px]" style={{ color: '#6b3fa0' }}>
          Upload your papers, rubrics, or requirements to get started.
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
