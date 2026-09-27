/// <reference types="vite/client" />

// Environment variables exposed by Vite are declared here so TypeScript
// knows about them. Add new VITE_* variables to .env.example as well.
interface ImportMetaEnv {
  /**
   * Backend API origin including the /api prefix,
   * e.g. http://localhost:8000/api (local) or
   * https://<backend-host>/api (production).
   *
   * Optional in local development (src/services/api.ts falls back to the
   * Django dev server); production builds must define it in the hosting
   * platform's environment variables before `npm run build`.
   */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
