import { Link, NavLink } from 'react-router-dom';
import Button from '../common/Button';

const navItems = [
  { to: '/', label: 'Home' },
  { to: '/chatbot', label: 'Chatbot' },
];

// Top bar: brand, primary navigation and the main call to action.
export default function Header() {
  return (
    <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center justify-between gap-4 border-b border-slate-200 bg-white/90 px-4 backdrop-blur md:px-6">
      <Link to="/" className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-sm font-bold text-white shadow-sm">
          N
        </span>
        <span className="flex flex-col leading-tight">
          <span className="text-base font-semibold tracking-tight text-slate-900">Nexus</span>
          <span className="hidden text-[11px] text-slate-500 sm:block">
            AI Academic Document Assistant
          </span>
        </span>
      </Link>

      <div className="flex items-center gap-1 sm:gap-2">
        <nav className="mr-1 hidden items-center gap-1 sm:flex">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-slate-100 font-medium text-slate-900'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <Button to="/chatbot" size="sm">
          Open Chatbot
        </Button>
      </div>
    </header>
  );
}
