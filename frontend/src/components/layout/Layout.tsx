import { Outlet } from 'react-router-dom';
import Header from './Header';

// Shared application shell: sticky header + routed page content.
// No sidebar — Chatbot manages its own internal panel.
export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex min-w-0 flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  );
}
