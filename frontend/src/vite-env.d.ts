/// <reference types="vite/client" />

// Environment variables exposed by Vite are declared here so TypeScript
// knows about them. Add new VITE_* variables to .env.example as well.
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
