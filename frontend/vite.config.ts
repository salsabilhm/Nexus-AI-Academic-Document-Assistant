import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite configuration for the Nexus frontend.
// The backend URL is never hardcoded here: it comes from VITE_API_BASE_URL.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
