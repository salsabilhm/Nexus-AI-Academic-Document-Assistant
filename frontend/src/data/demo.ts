import type { Message } from '../types/chat';
import type { DocumentItem } from '../types/document';

// ---------------------------------------------------------------------------
// Local mock data used ONLY to demonstrate the UI.
//
// createDemoReply() exists for reviewing the citation block offline. The
// document list below is not rendered anywhere: "My Documents" reads the
// documents of the current chat session from GET /api/documents/ instead, so
// the sidebar is never seeded with sample data.
// Nothing here is produced by a model or a server.
//
// CHAT_DEMO_MODE is false: POST /api/chat/ exists, so useChat calls
// chatbotApi.sendMessage() and renders the reply the backend stored. Flip it
// back to true only to review the chat UI without a backend running.
// ---------------------------------------------------------------------------
export const CHAT_DEMO_MODE: boolean = false;

/** Sample documents kept only for offline UI previews (never shown in the app). */
export const DEMO_DOCUMENTS: DocumentItem[] = [
  {
    id: 'doc-1',
    name: 'Thesis Requirements 2026.pdf',
    type: 'requirement',
    source: 'university',
    status: 'ready',
    createdAt: '2026-09-18T09:00:00.000Z',
  },
  {
    id: 'doc-2',
    name: 'Faculty Writing Guidelines.pdf',
    type: 'guideline',
    source: 'university',
    status: 'ready',
    createdAt: '2026-09-19T14:30:00.000Z',
  },
  {
    id: 'doc-3',
    name: 'Research Draft v3.docx',
    type: 'research',
    source: 'student',
    status: 'processing',
    createdAt: '2026-09-22T11:15:00.000Z',
  },
];

/** Starter questions offered in the chatbot empty state. */
export const DEMO_SUGGESTIONS: string[] = [
  'What does the university require in the methodology section?',
  'Which sections am I missing in my research draft?',
  'Compare my structure with the faculty guidelines.',
];

/**
 * Placeholder assistant reply (local data, not a model output) shown only
 * while CHAT_DEMO_MODE is true. The sources mirror DEMO_DOCUMENTS so the
 * citation UI can be reviewed with realistic values.
 */
export function createDemoReply(): Message {
  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    content:
      'This is a placeholder answer — the chat endpoint is not connected yet, so this reply comes from local demo data.\n\n' +
      'It shows how a real answer will look: for example, your methodology section describes the sampling method but does not yet justify the sample size required by the university guidelines (§4.2). Adding two sentences there would close the gap.',
    sources: [
      {
        documentId: 'doc-1',
        documentName: 'Thesis Requirements 2026.pdf',
        excerpt: '§4.2 — The methodology must state and justify the chosen sample size.',
        pageNumber: 12,
      },
      {
        documentId: 'doc-3',
        documentName: 'Research Draft v3.docx',
        excerpt: '3.1 Sampling — A convenience sample of 120 final-year students was selected.',
      },
    ],
    createdAt: new Date().toISOString(),
  };
}
