import ChatWindow from '../components/chatbot/ChatWindow';
import ChatInput from '../components/chatbot/ChatInput';
import DocumentUpload from '../components/documents/DocumentUpload';
import DocumentList from '../components/documents/DocumentList';
import ErrorMessage from '../components/common/ErrorMessage';
import { useChat } from '../hooks/useChat';
import { useDocuments } from '../hooks/useDocuments';
import { CHAT_DEMO_MODE, DEMO_SUGGESTIONS } from '../data/demo';

// Main Nexus interface: document panel on the side, conversation in the middle,
// question input at the bottom. Full-height layout — each pane scrolls itself.
export default function Chatbot() {
  const { documents, addLocalDocument } = useDocuments();
  const { messages, isSending, error, sendMessage, clearError } = useChat();

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col overflow-hidden p-4 md:p-6">
      <div className="grid min-h-0 flex-1 grid-rows-[auto_minmax(0,1fr)] gap-4 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)] lg:grid-rows-1">
        {/* Documents ---------------------------------------------------- */}
        <aside className="card flex max-h-[38vh] min-h-0 flex-col gap-4 overflow-y-auto p-4 lg:max-h-full">
          <div>
            <p className="section-label">Documents</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-500">
              Requirements and research used as context for your questions.
            </p>
          </div>

          <DocumentUpload compact onFileSelected={(file) => addLocalDocument(file.name)} />

          <div className="min-h-0">
            <DocumentList documents={documents} />
          </div>
        </aside>

        {/* Conversation -------------------------------------------------- */}
        <section className="card flex min-h-0 flex-col overflow-hidden">
          <header className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3 md:px-5">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 text-sm font-bold text-white">
                N
              </span>
              <div>
                <h1 className="text-sm font-semibold text-slate-900">Nexus Assistant</h1>
                <p className="text-xs text-slate-500">Answers grounded in your documents</p>
              </div>
            </div>

            <span className="pill hidden bg-slate-100 text-slate-600 sm:inline-flex">
              {messages.length === 0 ? 'New conversation' : `${messages.length} messages`}
            </span>
          </header>

          {CHAT_DEMO_MODE && (
            <div className="flex shrink-0 items-start gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs leading-relaxed text-amber-800 md:px-5">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                className="mt-0.5 h-3.5 w-3.5 shrink-0"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="9" />
                <path d="M12 8v4M12 16h.01" />
              </svg>
              <span>
                <strong className="font-semibold">Preview mode.</strong> The chat endpoint is not
                connected yet — replies below come from local demo data.
              </span>
            </div>
          )}

          <div className="min-h-0 flex-1">
            <ChatWindow
              messages={messages}
              isSending={isSending}
              suggestions={DEMO_SUGGESTIONS}
              onSelectSuggestion={sendMessage}
            />
          </div>

          {error && (
            <div className="shrink-0 px-4 pb-2 md:px-5">
              <ErrorMessage message={error} onDismiss={clearError} />
            </div>
          )}

          <div className="shrink-0">
            <ChatInput onSend={sendMessage} disabled={isSending} />
          </div>
        </section>
      </div>
    </div>
  );
}
