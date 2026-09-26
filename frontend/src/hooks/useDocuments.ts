import { useCallback, useState } from 'react';
import type { DocumentItem, DocumentSource } from '../types/document';
import { listDocuments, uploadDocument } from '../services/documentApi';
import { toApiError } from '../services/api';

// State container for the "My Documents" sidebar.
//
// The list belongs to ONE chat session:
// - `sessionId` is the conversation currently open. It is null right after
//   the page loads or after "New session", and the list then starts empty.
// - `onSessionId` hands the id back to the parent, because the backend (not
//   this hook) decides when a session starts: the first upload of a
//   conversation opens it and answers with its session_id.
//
// Nothing is ever deleted when the session changes — documents of earlier
// sessions keep their own session_id and are simply not shown here.
export function useDocuments(
  sessionId: string | null,
  onSessionId: (id: string) => void,
) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Re-read the documents of a session (GET /api/documents/?session_id=…).
   * Without a session there is nothing to fetch, so the list stays empty —
   * a brand-new conversation has no documents yet.
   */
  const refresh = useCallback(
    async (id: string | null = sessionId) => {
      if (!id) {
        setDocuments([]);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        setDocuments(await listDocuments(id));
      } catch (err) {
        setError(toApiError(err).message);
      } finally {
        setLoading(false);
      }
    },
    [sessionId],
  );

  /**
   * Upload a document file (.pdf/.doc/.docx/.zip) to the backend
   * (POST /api/documents/upload/) together with the current session id.
   *
   * On success the returned DocumentItem is prepended to the list so the UI
   * reflects the upload immediately, and the session's list is re-read from
   * the API so the sidebar matches what was stored.
   *
   * On failure the error is surfaced and no local state is mutated.
   *
   * Returns the created DocumentItem on success.
   */
  const uploadLocalDocument = useCallback(
    async (file: File, source: DocumentSource): Promise<DocumentItem | null> => {
      setLoading(true);
      setError(null);
      try {
        const item = await uploadDocument({ file, source, sessionId });

        // Very first upload of a conversation: the backend opened the session
        // and returned its id, which every later upload/question must reuse.
        if (item.sessionId && item.sessionId !== sessionId) {
          onSessionId(item.sessionId);
        }

        // Show it at once, then refresh the session's list from the server.
        setDocuments((previous) => [item, ...previous]);
        await refresh(item.sessionId ?? sessionId);
        return item;
      } catch (err) {
        const apiErr = toApiError(err);
        setError(apiErr.message);
        // Re-throw so DocumentUpload.handleConfirm can show the error in-component.
        throw new Error(apiErr.message);
      } finally {
        setLoading(false);
      }
    },
    [sessionId, onSessionId, refresh],
  );

  /** Forget the current session's documents ("New session"). */
  const resetDocuments = useCallback(() => {
    setDocuments([]);
    setError(null);
    setLoading(false);
  }, []);

  return { documents, loading, error, refresh, uploadLocalDocument, resetDocuments };
}
