import type { DocumentItem, UploadDocumentPayload } from '../types/document';
import api from './api';

// ---------------------------------------------------------------------------
// Response shape from POST /api/documents/upload/ and GET /api/documents/
// ---------------------------------------------------------------------------
interface UploadResponse {
  id: string;
  name: string;
  source: 'university' | 'student';
  status: 'uploaded' | 'processing' | 'ready' | 'failed';
  created_at: string;
  /** Chat session this document belongs to (opened by the upload if needed). */
  session_id: string | null;
}

// ---------------------------------------------------------------------------
// Map the API response to the frontend DocumentItem shape
// ---------------------------------------------------------------------------
function toDocumentItem(data: UploadResponse): DocumentItem {
  return {
    id: data.id,
    name: data.name,
    source: data.source,
    // The backend doesn't return `type`; derive a sensible default from source.
    type: data.source === 'university' ? 'requirement' : 'research',
    status: data.status,
    createdAt: data.created_at,
    sessionId: data.session_id ?? undefined,
  };
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

/**
 * Upload a document file to the backend (.pdf, .doc, .docx or .zip).
 *
 * Sends a multipart/form-data POST to POST /api/documents/upload/ with:
 *   file       — the File object (pdf/doc/docx/zip)
 *   source     — "university" | "student"
 *   session_id — the current chat session (when one exists yet), so the file
 *                is stored against the conversation it was added to
 *
 * The response carries the session the backend stored the file in — on the
 * very first upload that is a session the backend just opened, and the caller
 * adopts it as its current session.
 *
 * Returns the created DocumentItem on success.
 * Throws an Axios error on failure (use toApiError() from api.ts to normalise).
 */
export async function uploadDocument(payload: UploadDocumentPayload): Promise<DocumentItem> {
  const form = new FormData();
  form.append('file', payload.file);
  form.append('source', payload.source);
  if (payload.sessionId) {
    form.append('session_id', payload.sessionId);
  }

  // Do NOT set Content-Type manually — axios + FormData must let the browser
  // generate it automatically so the multipart boundary is included, e.g.:
  //   Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
  // Without the boundary Django's parser cannot split the parts and returns 400.
  const { data } = await api.post<UploadResponse>('/documents/upload/', form, {
    // Give large files more time than the default 30 s.
    timeout: 120_000,
  });

  return toDocumentItem(data);
}

/**
 * Fetch the documents uploaded during one chat session.
 *
 * GET /api/documents/?session_id=<uuid> — the backend returns only the files
 * stored against that session, so the sidebar can never leak documents from a
 * previous conversation. Newest first.
 */
export async function listDocuments(sessionId: string): Promise<DocumentItem[]> {
  const { data } = await api.get<UploadResponse[]>('/documents/', {
    params: { session_id: sessionId },
  });

  return data.map(toDocumentItem);
}

/**
 * Delete a document by ID.
 * TODO: implement once DELETE /api/documents/<id>/ exists.
 */
export async function deleteDocument(id: string): Promise<void> {
  throw new Error(`deleteDocument: not implemented yet (id: ${id}).`);
}
