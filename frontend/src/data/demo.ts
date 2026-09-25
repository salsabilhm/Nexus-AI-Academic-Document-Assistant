import type { Message } from '../types/chat';
import type { DocumentItem } from '../types/document';

// ---------------------------------------------------------------------------
// Local mock data used ONLY to demonstrate the UI.
//
// There is no backend chat/document endpoint yet, so without these values the
// interface could not show what a conversation, a document list or a citation
// block looks like. Nothing here is produced by a model or a server.
//
// Set CHAT_DEMO_MODE to false as soon as POST /api/chat/ exists: useChat will
// then call chatbotApi.sendMessage() instead of these placeholders.
// ---------------------------------------------------------------------------
export const CHAT_DEMO_MODE: boolean = true;

/** Placeholder document list until GET /api/documents/ is implemented. */
export const DEMO_DOCUMENTS: DocumentItem[] = [
  {
    id: 'doc-1',
    name: 'Thesis Requirements 2026.pdf',
    type: 'requirement',
    status: 'ready',
    createdAt: '2026-09-18T09:00:00.000Z',
  },
  {
    id: 'doc-2',
    name: 'Faculty Writing Guidelines.pdf',
    type: 'guideline',
    status: 'ready',
    createdAt: '2026-09-19T14:30:00.000Z',
  },
  {
    id: 'doc-3',
    name: 'Research Draft v3.docx',
    type: 'research',
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
 * Placeholder assistant reply (local data, not a model output) shown while
 * CHAT_DEMO_MODE is true. The sources mirror DEMO_DOCUMENTS so the citation UI
 * can be reviewed with realistic values.
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
