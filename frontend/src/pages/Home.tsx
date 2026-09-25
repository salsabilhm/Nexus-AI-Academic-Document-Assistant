import type { ReactNode } from 'react';
import DocumentUpload from '../components/documents/DocumentUpload';
import DocumentList from '../components/documents/DocumentList';
import Button from '../components/common/Button';
import { useDocuments } from '../hooks/useDocuments';

interface Capability {
  title: string;
  description: string;
  icon: ReactNode;
}

const iconProps = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  className: 'h-5 w-5',
  'aria-hidden': true,
};

const capabilities: Capability[] = [
  {
    title: 'Find university requirements',
    description: 'Locate the rules that apply to your submission: structure, sections and formatting.',
    icon: (
      <svg {...iconProps}>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.6-3.6" />
      </svg>
    ),
  },
  {
    title: 'Retrieve relevant research content',
    description: 'Pull the passages from your own documents that matter for the question.',
    icon: (
      <svg {...iconProps}>
        <path d="M14 3v5h5" />
        <path d="M19 8v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5z" />
        <path d="M9 13h6M9 17h4" />
      </svg>
    ),
  },
  {
    title: 'Compare requirements with research',
    description: 'Check your work against what the university actually asks for.',
    icon: (
      <svg {...iconProps}>
        <path d="M12 3v18M5 7h14" />
        <path d="m7 7-3 6a3 3 0 0 0 6 0L7 7zM17 7l-3 6a3 3 0 0 0 6 0l-3-6z" />
      </svg>
    ),
  },
  {
    title: 'Identify missing or unclear sections',
    description: 'Spot gaps and vague parts before your supervisor does.',
    icon: (
      <svg {...iconProps}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8v4M12 16h.01" />
      </svg>
    ),
  },
  {
    title: 'Show sources',
    description: 'Every answer cites the document, page and excerpt it came from.',
    icon: (
      <svg {...iconProps}>
        <path d="M10 13a5 5 0 0 0 7.07 0l2.83-2.83a5 5 0 0 0-7.07-7.07L11.4 4.6" />
        <path d="M14 11a5 5 0 0 0-7.07 0L4.1 13.83a5 5 0 0 0 7.07 7.07L12.6 19.4" />
      </svg>
    ),
  },
];

// Landing page: product intro, capabilities, document upload, way into chat.
export default function Home() {
  const { documents, addLocalDocument } = useDocuments();

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10 md:px-8 md:py-16">
      {/* Hero ------------------------------------------------------------- */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-x-0 -top-32 h-72 bg-gradient-to-b from-indigo-100/70 to-transparent" />

        <div className="relative grid items-center gap-10 md:grid-cols-2">
          <div>
            <span className="pill bg-indigo-50 text-indigo-700">
              <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
              AI academic assistant
            </span>

            <h1 className="mt-4 font-serif text-4xl font-semibold tracking-tight text-slate-900 md:text-5xl">
              Nexus
            </h1>
            <p className="mt-3 text-lg leading-relaxed text-slate-600">
              Check your research against university requirements — and see the source behind
              every answer.
            </p>
            <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-500">
              Upload requirements, guidelines and your own draft. Nexus retrieves the relevant
              passages, compares them with your work and points out what is missing or unclear.
            </p>

            <div className="mt-7 flex flex-wrap items-center gap-3">
              <Button to="/chatbot" size="lg">
                Start Analysis
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-4 w-4"
                  aria-hidden="true"
                >
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </Button>
              <Button to="/chatbot" variant="secondary" size="lg">
                Open Chatbot
              </Button>
            </div>

            <ul className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500">
              {['Answers grounded in your files', 'Sources with every reply', 'Built for students'].map(
                (item) => (
                  <li key={item} className="flex items-center gap-1.5">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-3.5 w-3.5 text-indigo-500"
                      aria-hidden="true"
                    >
                      <path d="m5 13 4 4L19 7" />
                    </svg>
                    {item}
                  </li>
                ),
              )}
            </ul>
          </div>

          {/* Static illustration of an answer with citations. */}
          <div className="card p-5 shadow-md">
            <div className="flex items-center justify-between">
              <span className="section-label">Example</span>
              <span className="pill bg-indigo-50 text-indigo-600">answer + sources</span>
            </div>

            <div className="mt-4 flex justify-end">
              <p className="max-w-[85%] rounded-2xl rounded-br-md bg-indigo-600 px-3 py-2 text-xs text-white">
                Is my methodology section complete?
              </p>
            </div>

            <div className="mt-3 flex gap-2">
              <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 text-[10px] font-bold text-white">
                N
              </span>
              <div className="min-w-0 flex-1 rounded-xl rounded-bl-md border border-slate-200 bg-white px-3 py-2.5">
                <p className="text-xs leading-relaxed text-slate-700">
                  Partly. Section 3.1 describes the sampling method but does not justify the
                  sample size required by §4.2.
                </p>

                <p className="section-label mt-2.5">Sources</p>
                <ol className="mt-1.5 space-y-1">
                  <li className="flex gap-1.5 rounded-lg bg-slate-50 px-2 py-1.5 text-[11px] text-slate-500">
                    <span className="font-semibold text-indigo-600">1</span>
                    <span>
                      <span className="font-medium text-slate-700">
                        Thesis Requirements 2026.pdf
                      </span>{' '}
                      · p. 12
                    </span>
                  </li>
                  <li className="flex gap-1.5 rounded-lg bg-slate-50 px-2 py-1.5 text-[11px] text-slate-500">
                    <span className="font-semibold text-indigo-600">2</span>
                    <span>
                      <span className="font-medium text-slate-700">Research Draft v3.docx</span> ·
                      §3.1
                    </span>
                  </li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Capabilities ----------------------------------------------------- */}
      <section className="mt-16 md:mt-24">
        <p className="section-label">What Nexus can do</p>
        <h2 className="mt-2 max-w-2xl text-2xl font-semibold tracking-tight text-slate-900 md:text-3xl">
          From a pile of PDFs to a clear answer
        </h2>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((capability) => (
            <div
              key={capability.title}
              className="card p-5 transition-colors hover:border-indigo-200"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                {capability.icon}
              </span>
              <h3 className="mt-4 text-sm font-semibold text-slate-900">{capability.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-500">
                {capability.description}
              </p>
            </div>
          ))}

          <div className="flex flex-col justify-between rounded-2xl border border-dashed border-slate-300 p-5">
            <p className="text-sm leading-relaxed text-slate-600">
              Ready to try it on your own documents?
            </p>
            <Button to="/chatbot" variant="secondary" className="mt-4 self-start">
              Start Analysis →
            </Button>
          </div>
        </div>
      </section>

      {/* Upload ------------------------------------------------------------ */}
      <section className="mt-16 md:mt-24">
        <p className="section-label">Get started</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900 md:text-3xl">
          Bring your documents
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
          Add the university requirements and your research draft. Documents stay in your workspace
          and are only used to ground the answers you ask for.
        </p>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="space-y-3">
            <DocumentUpload onFileSelected={(file) => addLocalDocument(file.name)} />
          </div>

          <div className="card p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="section-label">Your documents</p>
              <span className="pill bg-slate-100 text-slate-600">{documents.length}</span>
            </div>
            <DocumentList documents={documents} />
          </div>
        </div>
      </section>

      <footer className="mt-16 border-t border-slate-200 pt-6 text-xs text-slate-400">
        Nexus — AI Academic Document Assistant · frontend preview, no AI services connected yet.
      </footer>
    </div>
  );
}
