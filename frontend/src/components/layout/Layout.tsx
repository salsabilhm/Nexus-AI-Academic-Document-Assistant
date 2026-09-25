import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

// Shared application shell: sticky header on top, sidebar on the left and the
// routed page in the main area. Pages own their own padding and scrolling —
// this keeps full-height layouts (like the chatbot) possible.
export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="flex min-w-0 flex-1 flex-col">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
