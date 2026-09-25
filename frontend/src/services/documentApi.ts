import type { DocumentItem } from '../types/document';

// Document-related API calls.
//
// TODO(document endpoints): the backend does not expose document routes yet
// (no upload/list/delete endpoints exist). These placeholders define the
// contract the frontend will use once they are implemented — they do not
// perform any request on purpose, so we never call URLs that do not exist.

export async function listDocuments(): Promise<DocumentItem[]> {
  throw new Error('listDocuments: document endpoints are not implemented yet.');
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  throw new Error(`uploadDocument: not implemented yet (file: ${file.name}).`);
}

export async function deleteDocument(id: string): Promise<void> {
  throw new Error(`deleteDocument: not implemented yet (id: ${id}).`);
}
