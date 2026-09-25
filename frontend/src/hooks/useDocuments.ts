import { useCallback, useState } from 'react';
import type { DocumentItem, DocumentType } from '../types/document';
import { listDocuments } from '../services/documentApi';
import { toApiError } from '../services/api';
import { DEMO_DOCUMENTS } from '../data/demo';

// Rough guess so the demo list looks sensible; the backend will classify
// documents properly once POST /api/documents/ exists.
function guessDocumentType(name: string): DocumentType {
  const lower = name.toLowerCase();
  if (lower.includes('thesis')) return 'thesis';
  if (lower.includes('research') || lower.includes('draft')) return 'research';
  if (lower.includes('template')) return 'template';
  if (lower.includes('guideline') || lower.includes('guide')) return 'guideline';
  return 'requirement';
}

// State container for the document list.
//
// Starts from local demo data (DEMO_DOCUMENTS) so the UI can be reviewed;
// refresh() will replace it with the real list once GET /api/documents/ exists.
export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentItem[]>(DEMO_DOCUMENTS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // TODO: call this once the backend exposes GET document endpoints.
  // Until then it fails with an explicit "not implemented" message.
  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await listDocuments();
      setDocuments(items);
    } catch (err) {
      setError(toApiError(err).message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Local-only placeholder: adds the chosen file to the list so the upload
  // area can be demonstrated. No request is sent anywhere.
  const addLocalDocument = useCallback((name: string) => {
    const item: DocumentItem = {
      id: crypto.randomUUID(),
      name,
      type: guessDocumentType(name),
      status: 'uploaded',
      createdAt: new Date().toISOString(),
    };
    setDocuments((previous) => [item, ...previous]);
  }, []);

  return { documents, loading, error, refresh, addLocalDocument };
}
