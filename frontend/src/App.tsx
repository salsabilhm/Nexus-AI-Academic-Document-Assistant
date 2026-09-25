import { Route, Routes } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import Chatbot from './pages/Chatbot';

// Route table. Every page renders inside the shared Layout.
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="chatbot" element={<Chatbot />} />
      </Route>
    </Routes>
  );
}
