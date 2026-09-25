// Types describing a document handled by Nexus.
// The backend will own the canonical shape; this mirrors the API contract.

export type DocumentType = 'requirement' | 'guideline' | 'template' | 'research' | 'thesis';

export type DocumentStatus = 'uploaded' | 'processing' | 'ready' | 'failed';

// Named DocumentItem (not Document) to avoid clashing with the DOM lib type.
export interface DocumentItem {
  id: string;
  name: string;
  type: DocumentType;
  status: DocumentStatus;
  createdAt: string;
}
