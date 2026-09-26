import { Link } from 'react-router-dom';
import NexusLogo from '../components/common/NexusLogo';

// ------------------------------------------------------------------ //
// Feature cards data                                                   //
// ------------------------------------------------------------------ //
const features = [
  {
    title: 'Document Retrieval',
    description: 'Upload your research papers and academic briefs. Nexus surfaces the exact passages that matter, in seconds.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
        <path d="M14 3v5h5" />
        <path d="M19 8v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5z" />
        <path d="M9 13h6M9 17h4" />
      </svg>
    ),
  },
  {
    title: 'AI Analysis',
    description: 'Ask plain-language questions and get grounded, cited answers drawn directly from your documents.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v3M12 20v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M1 12h3M20 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12" />
      </svg>
    ),
  },
  {
    title: 'Requirement Comparison',
    description: 'Compare your work against academic requirements and instantly see what\'s missing, met, or exceeds expectations.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
        <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
      </svg>
    ),
  },
];

const steps = [
  { num: '01', title: 'Upload your documents', desc: 'Add your university rubrics, guidelines, and research drafts.' },
  { num: '02', title: 'Ask in plain language', desc: 'Type any question about your research or requirements.' },
  { num: '03', title: 'Get cited answers', desc: 'Every response includes document excerpts and page numbers.' },
];

// ------------------------------------------------------------------ //
// Home Page                                                            //
// ------------------------------------------------------------------ //
export default function Home() {
  return (
    <div style={{ background: '#0d0014', minHeight: '100vh' }}>

      {/* ----------------------------------------------------------------
          Hero section
      ---------------------------------------------------------------- */}
      <section className="relative overflow-hidden">
        {/* Background glow */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background: 'radial-gradient(ellipse at 70% 30%, rgba(124,58,237,0.18) 0%, transparent 60%), radial-gradient(ellipse at 20% 80%, rgba(232,121,249,0.08) 0%, transparent 50%)',
          }}
          aria-hidden="true"
        />

        <div className="relative mx-auto flex max-w-6xl flex-col items-center gap-10 px-5 py-20 md:flex-row md:gap-16 md:py-28 lg:px-8">
          {/* Left: text */}
          <div className="flex-1 animate-fade-up" style={{ animationDelay: '0ms' }}>
            <div className="nx-pill mb-6 w-fit">
              <span className="h-1.5 w-1.5 rounded-full bg-purple-400" />
              AI Academic Assistant
            </div>

            <h1
              className="mb-5 font-display leading-none tracking-tight"
              style={{
                fontSize: 'clamp(3.5rem, 8vw, 7rem)',
                fontWeight: 700,
                background: 'linear-gradient(135deg, #f0e4ff 0%, #c084fc 45%, #7c3aed 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              Nexus
            </h1>

            <p
              className="mb-8 max-w-lg text-lg leading-relaxed"
              style={{ color: '#c4a8e0' }}
            >
              Nexus helps university students understand and compare academic requirements
              with their research documents using AI-powered document retrieval and analysis.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              <Link to="/chatbot" className="nx-btn-primary px-7 py-3 text-base font-semibold">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                Start Chatting
              </Link>
              <a
                href="#features"
                className="nx-btn-secondary px-7 py-3 text-base"
              >
                Explore features
              </a>
            </div>

            {/* Trust badges */}
            <div className="mt-10 flex flex-wrap gap-5">
              {['Grounded answers', 'Cited sources', 'Built for students'].map((badge) => (
                <span key={badge} className="flex items-center gap-2 text-sm" style={{ color: '#a78bca' }}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="#c084fc" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
                    <path d="m5 13 4 4L19 7" />
                  </svg>
                  {badge}
                </span>
              ))}
            </div>
          </div>

          {/* Right: visual card */}
          <div
            className="w-full max-w-sm flex-shrink-0 animate-fade-up"
            style={{ animationDelay: '120ms' }}
          >
            <div
              className="relative overflow-hidden rounded-3xl p-px"
              style={{
                background: 'linear-gradient(135deg, rgba(192,132,252,0.35) 0%, rgba(124,58,237,0.15) 60%, transparent 100%)',
              }}
            >
              <div
                className="rounded-3xl p-6"
                style={{ background: 'linear-gradient(160deg, #1a0028 0%, #130020 100%)' }}
              >
                {/* Logo centrepiece */}
                <div className="flex items-center justify-center py-8">
                  <div
                    className="relative flex h-28 w-28 items-center justify-center rounded-3xl"
                    style={{
                      background: 'linear-gradient(145deg, #2e1050 0%, #1a0028 100%)',
                      boxShadow: '0 0 40px rgba(192,132,252,0.25)',
                    }}
                  >
                    <NexusLogo size={72} />
                    {/* Orbit ring decoration */}
                    <svg className="pointer-events-none absolute inset-0 h-full w-full animate-pulse-slow" viewBox="0 0 112 112" fill="none" aria-hidden="true">
                      <circle cx="56" cy="56" r="52" stroke="rgba(192,132,252,0.12)" strokeWidth="1" />
                      <circle cx="56" cy="56" r="44" stroke="rgba(232,121,249,0.08)" strokeWidth="1" strokeDasharray="4 8" />
                    </svg>
                  </div>
                </div>

                {/* Mock chat snippet */}
                <div className="mt-2 space-y-3">
                  <div className="flex justify-end">
                    <div
                      className="max-w-[85%] rounded-2xl rounded-br-md px-4 py-2.5 text-sm"
                      style={{ background: 'rgba(192,132,252,0.18)', color: '#e8d5f5', border: '1px solid rgba(192,132,252,0.2)' }}
                    >
                      Is my methodology complete?
                    </div>
                  </div>
                  <div className="flex gap-2.5">
                    <NexusLogo size={24} className="mt-0.5 flex-shrink-0" />
                    <div
                      className="rounded-2xl rounded-bl-md px-4 py-3 text-xs leading-relaxed"
                      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(192,132,252,0.12)', color: '#c4a8e0' }}
                    >
                      Partly. Section 3.1 describes the sampling method but doesn't justify sample size per §4.2.
                      <div className="mt-2 flex items-center gap-1.5" style={{ color: '#7c3aed' }}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" className="h-3 w-3" aria-hidden="true">
                          <path d="M10 13a5 5 0 0 0 7.07 0l2.83-2.83a5 5 0 0 0-7.07-7.07L11.4 4.6" />
                          <path d="M14 11a5 5 0 0 0-7.07 0L4.1 13.83a5 5 0 0 0 7.07 7.07L12.6 19.4" />
                        </svg>
                        <span className="text-[10px]">2 sources · p.12</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------
          Features section
      ---------------------------------------------------------------- */}
      <section id="features" className="mx-auto max-w-6xl px-5 py-20 lg:px-8">
        <div className="mb-3 nx-label">Three capabilities</div>
        <h2
          className="mb-4 text-3xl font-bold tracking-tight md:text-4xl"
          style={{ color: '#f0e4ff' }}
        >
          Built for academic clarity
        </h2>
        <p className="mb-12 max-w-xl text-base leading-relaxed" style={{ color: '#a78bca' }}>
          Three capabilities that turn a stack of documents into clear, confident answers.
        </p>

        <div className="grid gap-5 sm:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="group rounded-2xl p-6 transition-all duration-300"
              style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(192,132,252,0.12)',
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(192,132,252,0.3)';
                (e.currentTarget as HTMLDivElement).style.background = 'rgba(192,132,252,0.06)';
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(192,132,252,0.12)';
                (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.03)';
              }}
            >
              <div
                className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl"
                style={{ background: 'rgba(192,132,252,0.12)', color: '#c084fc' }}
              >
                {feature.icon}
              </div>
              <h3 className="mb-2 font-semibold" style={{ color: '#f0e4ff' }}>{feature.title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: '#8b6ab0' }}>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ----------------------------------------------------------------
          How it works
      ---------------------------------------------------------------- */}
      <section className="mx-auto max-w-6xl px-5 pb-20 lg:px-8">
        <div
          className="relative overflow-hidden rounded-3xl p-px"
          style={{ background: 'linear-gradient(135deg, rgba(192,132,252,0.25) 0%, rgba(124,58,237,0.1) 100%)' }}
        >
          <div
            className="relative rounded-3xl p-10 md:p-14"
            style={{ background: 'linear-gradient(160deg, #1a0028 0%, #130020 100%)' }}
          >
            {/* Background glow */}
            <div
              className="pointer-events-none absolute inset-0 rounded-3xl"
              style={{ background: 'radial-gradient(ellipse at 80% 20%, rgba(124,58,237,0.15) 0%, transparent 60%)' }}
              aria-hidden="true"
            />

            <div className="relative grid gap-10 md:grid-cols-2 md:items-center">
              <div>
                <h2
                  className="mb-4 text-3xl font-bold leading-tight md:text-4xl"
                  style={{ color: '#f0e4ff' }}
                >
                  Your research,{' '}
                  <span style={{ color: '#c084fc' }}>understood.</span>
                </h2>
                <p className="mb-8 leading-relaxed" style={{ color: '#a78bca' }}>
                  Stop scrolling through dozens of PDFs. Drop your documents into Nexus, ask
                  anything, and get answers grounded in your own sources — with the citations to
                  prove it.
                </p>
                <Link to="/chatbot" className="nx-btn-primary px-7 py-3 text-base font-semibold">
                  Open Nexus
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
                    <path d="M5 12h14M13 6l6 6-6 6" />
                  </svg>
                </Link>
              </div>

              {/* Steps */}
              <div className="space-y-5">
                {steps.map((step) => (
                  <div key={step.num} className="flex items-start gap-4">
                    <span
                      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                      style={{ background: 'rgba(192,132,252,0.12)', color: '#c084fc', border: '1px solid rgba(192,132,252,0.2)' }}
                    >
                      {step.num}
                    </span>
                    <div>
                      <p className="font-semibold" style={{ color: '#f0e4ff' }}>{step.title}</p>
                      <p className="mt-0.5 text-sm leading-relaxed" style={{ color: '#8b6ab0' }}>{step.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------
          Footer
      ---------------------------------------------------------------- */}
      <footer
        className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-6 lg:px-8"
        style={{ borderTop: '1px solid rgba(192,132,252,0.1)' }}
      >
        <div className="flex items-center gap-2">
          <NexusLogo size={20} />
          <span className="text-sm font-semibold" style={{ color: '#f0e4ff' }}>Nexus</span>
        </div>
        <p className="text-xs" style={{ color: '#4a2870' }}>
          Nexus — AI Academic Document Assistant. Built for students.
        </p>
      </footer>
    </div>
  );
}
