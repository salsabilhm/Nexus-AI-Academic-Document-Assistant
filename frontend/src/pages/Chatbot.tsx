import { useCallback, useState } from 'react';
import { Link } from 'react-router-dom';
import ChatWindow from '../components/chatbot/ChatWindow';
import ChatInput from '../components/chatbot/ChatInput';
import DocumentUpload from '../components/documents/DocumentUpload';
import DocumentList from '../components/documents/DocumentList';
import ErrorMessage from '../components/common/ErrorMessage';
import NexusLogo from '../components/common/NexusLogo';
import { useChat } from '../hooks/useChat';
import { useDocuments } from '../hooks/useDocuments';
import { CHAT_DEMO_MODE, DEMO_SUGGESTIONS } from '../data/demo';

// Full-height chatbot: narrow doc sidebar on the left, conversation on the right.
export default function Chatbot() {
  // The chat session currently open. null = a brand-new conversation: no
  // messages, no documents, and no chat_sessions row yet (the first question
  // or the first upload creates it and the id is fed back through the hooks).
  const [sessionId, setSessionId] = useState<string | null>(null);
  const { documents, uploadLocalDocument, resetDocuments } = useDocuments(sessionId, setSessionId);
  const { messages, isSending, error, sendMessage, clearError, resetChat } = useChat(
    sessionId,
    setSessionId,
  );
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // "New session": drop the session id, the conversation and the sidebar list.
  // Nothing is deleted server-side — the previous session and its documents
  // stay in PostgreSQL/Supabase Storage, they are just no longer displayed.
  const handleNewSession = useCallback(() => {
    setSessionId(null);
    resetChat();
    resetDocuments();
  }, [resetChat, resetDocuments]);

  return (
    <div
      className="flex"
      style={{ height: 'calc(100vh - 4rem)', background: '#0d0014' }}
    >
      {/* ----------------------------------------------------------------
          Document sidebar
      ---------------------------------------------------------------- */}
      <aside
        className="flex flex-col transition-all duration-300"
        style={{
          width: sidebarOpen ? '272px' : '0px',
          minWidth: sidebarOpen ? '272px' : '0px',
          overflow: 'hidden',
          borderRight: '1px solid rgba(192,132,252,0.1)',
          background: 'rgba(255,255,255,0.02)',
        }}
      >
        <div className="flex min-w-[272px] flex-1 flex-col overflow-y-auto p-4">
          {/* Sidebar header */}
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p
                className="text-xs font-semibold uppercase tracking-widest"
                style={{ color: '#a78bca' }}
              >
                My Documents
              </p>
            </div>
            <span
              className="flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold"
              style={{ background: 'rgba(192,132,252,0.15)', color: '#c084fc' }}
            >
              {documents.length}
            </span>
          </div>

          {/* Upload area */}
          <DocumentUpload
            compact
            onFileSelected={uploadLocalDocument}
          />

          {/* Doc list */}
          <div className="mt-3 min-h-0 flex-1 overflow-y-auto">
            <DocumentList documents={documents} />
          </div>

          {/* Demo mode notice */}
          {CHAT_DEMO_MODE && (
            <div
              className="mt-4 rounded-xl px-3 py-2.5 text-[11px] leading-relaxed"
              style={{
                background: 'rgba(251,191,36,0.08)',
                border: '1px solid rgba(251,191,36,0.15)',
                color: '#b45309',
              }}
            >
              <strong className="font-semibold" style={{ color: '#d97706' }}>Preview mode.</strong>
              {' '}Replies come from local demo data — backend not connected yet.
            </div>
          )}
        </div>
      </aside>

      {/* ----------------------------------------------------------------
          Main chat panel
      ---------------------------------------------------------------- */}
      <section className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Chat header */}
        <header
          className="flex shrink-0 items-center justify-between gap-3 px-4 py-3 md:px-5"
          style={{ borderBottom: '1px solid rgba(192,132,252,0.1)' }}
        >
          <div className="flex items-center gap-2">
            {/* Sidebar toggle */}
            <button
              type="button"
              onClick={() => setSidebarOpen((o) => !o)}
              aria-label={sidebarOpen ? 'Close document panel' : 'Open document panel'}
              className="flex h-8 w-8 items-center justify-center rounded-xl transition-all"
              style={{ color: '#7c3aed' }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = 'rgba(192,132,252,0.1)';
                (e.currentTarget as HTMLButtonElement).style.color = '#c084fc';
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
                (e.currentTarget as HTMLButtonElement).style.color = '#7c3aed';
              }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <path d="M9 3v18" />
              </svg>
            </button>

            {/* Back to home */}
            <Link
              to="/"
              className="flex items-center gap-1.5 text-sm transition-all"
              style={{ color: '#7c3aed' }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = '#c084fc'; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = '#7c3aed'; }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5" aria-hidden="true">
                <path d="m15 18-6-6 6-6" />
              </svg>
              Back
            </Link>
          </div>

          {/* Centre: brand */}
          <div className="flex items-center gap-2">
            <NexusLogo size={26} />
            <span className="text-sm font-semibold" style={{ color: '#f0e4ff' }}>Nexus</span>
          </div>

          {/* Online indicator */}
          <div className="flex items-center gap-1.5 text-xs" style={{ color: '#a78bca' }}>
            <span
              className="h-2 w-2 rounded-full animate-pulse"
              style={{ background: '#10b981' }}
            />
            Online
          </div>
        </header>

        {/* Messages */}
        <div className="min-h-0 flex-1 overflow-hidden">
          <ChatWindow
            messages={messages}
            isSending={isSending}
            suggestions={DEMO_SUGGESTIONS}
            onSelectSuggestion={sendMessage}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="shrink-0 px-4 pb-2 md:px-5">
            <ErrorMessage message={error} onDismiss={clearError} />
          </div>
        )}

        {/* Input */}
        <div className="shrink-0">
          <ChatInput
            onSend={sendMessage}
            onNewSession={handleNewSession}
            disabled={isSending}
          />
        </div>

        {/* Disclaimer */}
        <div
          className="shrink-0 py-1.5 text-center text-[11px]"
          style={{ color: 'rgba(192,132,252,0.25)', borderTop: '1px solid rgba(192,132,252,0.06)' }}
        >
          Nexus is a demo assistant. Responses are illustrative.
        </div>
      </section>
    </div>
  );
}
