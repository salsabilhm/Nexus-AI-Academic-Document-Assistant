import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Home', hint: 'Overview & upload' },
  { to: '/chatbot', label: 'Chatbot', hint: 'Ask about your documents' },
];

const steps = [
  'Upload university requirements and your research.',
  'Ask a question in plain language.',
  'Read the answer together with its sources.',
];

// Left navigation: route links plus a short "how to start" guide.
export default function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-slate-200 bg-white p-4 md:flex">
      <nav className="flex flex-col gap-1" aria-label="Main navigation">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex flex-col gap-0.5 rounded-xl px-3 py-2.5 transition-colors ${
                isActive
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            <span className="text-sm font-medium">{item.label}</span>
            <span className="text-[11px] opacity-70">{item.hint}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <p className="section-label mb-2">How to start</p>
        <ol className="space-y-2">
          {steps.map((step, index) => (
            <li key={step} className="flex gap-2 text-xs leading-relaxed text-slate-600">
              <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-white text-[10px] font-semibold text-indigo-600 ring-1 ring-slate-200">
                {index + 1}
              </span>
              {step}
            </li>
          ))}
        </ol>
      </div>

      <p className="mt-auto pt-4 text-[11px] leading-relaxed text-slate-400">
        Frontend preview — no AI services are connected yet.
      </p>
    </aside>
  );
}
