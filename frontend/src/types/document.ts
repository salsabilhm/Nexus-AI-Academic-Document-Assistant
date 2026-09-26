// Types describing a document handled by Nexus.
// The backend will own the canonical shape; this mirrors the API contract.

export type DocumentType = 'requirement' | 'guideline' | 'template' | 'research' | 'thesis';

export type DocumentStatus = 'uploaded' | 'processing' | 'ready' | 'failed';

/** Who provided the document: the university or the student. */
export type DocumentSource = 'university' | 'student';

// Named DocumentItem (not Document) to avoid clashing with the DOM lib type.
export interface DocumentItem {
  id: string;
  name: string;
  type: DocumentType;
  source: DocumentSource;
  status: DocumentStatus;
  createdAt: string;
  /** Chat session the document was uploaded in (never shown across sessions). */
  sessionId?: string;
}

/** Payload sent to POST /api/documents/upload/. */
export interface UploadDocumentPayload {
  file: File;
  source: DocumentSource;
  /**
   * Current chat session. Omit it on the very first upload of a conversation:
   * the backend then opens the session and answers with its session_id.
   */
  sessionId?: string | null;
}
