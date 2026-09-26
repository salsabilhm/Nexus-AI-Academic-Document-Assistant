import { Link, NavLink } from 'react-router-dom';
import NexusLogo from '../common/NexusLogo';

// Top navigation bar — dark glass with Nexus brand.
export default function Header() {
  return (
    <header
      className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between gap-4 px-5 md:px-8"
      style={{
        background: 'rgba(13, 0, 20, 0.85)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(192, 132, 252, 0.12)',
      }}
    >
      {/* Brand */}
      <Link to="/" className="flex items-center gap-2.5 group">
        <NexusLogo size={34} />
        <span className="flex flex-col leading-tight">
          <span
            className="text-sm font-semibold tracking-wide transition-colors group-hover:text-purple-300"
            style={{ color: '#f0e4ff' }}
          >
            Nexus
          </span>
          <span className="hidden text-[10px] sm:block" style={{ color: '#6b3fa0' }}>
            AI Academic Assistant
          </span>
        </span>
      </Link>

      {/* Right side */}
      <div className="flex items-center gap-2">
        <nav className="mr-2 hidden items-center gap-1 sm:flex" aria-label="Main navigation">
          {[
            { to: '/', label: 'Home' },
            { to: '/chatbot', label: 'Chatbot' },
          ].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `rounded-full px-4 py-1.5 text-sm font-medium transition-all ${
                  isActive
                    ? 'text-purple-200'
                    : 'text-purple-300/60 hover:text-purple-200'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <Link
          to="/chatbot"
          className="nx-btn-primary px-4 py-2 text-sm font-semibold"
        >
          Open Nexus
        </Link>
      </div>
    </header>
  );
}
