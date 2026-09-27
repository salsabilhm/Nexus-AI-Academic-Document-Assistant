import axios from 'axios';
import type { AxiosError } from 'axios';
import type { ApiError, HealthResponse } from '../types/api';

// ---------------------------------------------------------------------------
// Base URL resolution (single source of truth for every request)
// ---------------------------------------------------------------------------
// Order of precedence:
//   1. VITE_API_BASE_URL — read from import.meta.env. Vite inlines it at
//      BUILD time from frontend/.env (local `npm run dev`) or from the
//      hosting platform's environment variables (production builds, e.g.
//      Vercel → Project → Settings → Environment Variables →
//      VITE_API_BASE_URL=https://<backend-host>/api, then redeploy).
//   2. Local-development fallback — when the variable is missing on the
//      Vite dev server, use the Django dev server so `npm run dev` works
//      with zero configuration (no .env required).
//   3. Production builds never guess a host: a missing variable logs a loud,
//      actionable error instead of silently calling the frontend origin
//      (that is what produced the 404/405 responses).
const fromEnv: string = (import.meta.env.VITE_API_BASE_URL ?? '').trim();

if (!fromEnv) {
  if (import.meta.env.DEV) {
    console.info(
      '[Nexus] VITE_API_BASE_URL is not set — using the local fallback ' +
        'http://localhost:8000/api (create frontend/.env to override).',
    );
  } else {
    console.error(
      '[Nexus] VITE_API_BASE_URL was not set when this bundle was built.\n' +
        'Set it on the hosting platform (e.g. Vercel → Settings → Environment\n' +
        'Variables) and redeploy — Vite bakes env vars in at build time:\n' +
        '  VITE_API_BASE_URL=https://<backend-host>/api',
    );
  }
}

// Resolve: env var first, local dev fallback otherwise ('' in production
// without configuration — an error was already logged above).
let resolved: string =
  fromEnv || (import.meta.env.DEV ? 'http://localhost:8000/api' : '');

// Safety net: a production page whose API points at the user's OWN machine
// can never work (the backend lives on a server, not on their laptop). This
// catches the classic footgun of shipping an artifact that was built while
// frontend/.env still pointed at the dev server. `vite preview` keeps
// working: there the page itself is served from localhost.
const pointsAtOwnMachine = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?\b/i.test(resolved);
const servedFromLocalhost = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(
  window.location.hostname,
);
if (pointsAtOwnMachine && import.meta.env.PROD && !servedFromLocalhost) {
  console.error(
    '[Nexus] VITE_API_BASE_URL points at localhost in a production build ' +
      '— ignoring it.\nSet VITE_API_BASE_URL=https://<backend-host>/api in ' +
      'the hosting platform\n(e.g. Vercel → Settings → Environment ' +
      'Variables) and rebuild.',
  );
  resolved = '';
}

// All backend routes live under /api/ (config/urls.py), so flag a base URL
// that clearly forgot the prefix instead of letting it 404 confusingly.
if (resolved && !resolved.endsWith('/api')) {
  console.warn(
    `[Nexus] VITE_API_BASE_URL ("${resolved}") does not end with /api — ` +
      'requests will miss the Django API prefix.',
  );
}

// Strip any accidental trailing slash so paths like "/documents/upload/" keep
// matching Django's "/api/documents/upload/" routes (Django keeps its own
// trailing slashes; the frontend paths below all carry them too).
const API_BASE_URL = resolved.replace(/\/+$/, '');

// ---------------------------------------------------------------------------
// Axios client
// ---------------------------------------------------------------------------
// Central Axios instance. Every service (documentApi, chatbotApi) builds on
// this so the base URL, timeout, and error handling live in one place.
// No global Content-Type is set — axios sets 'application/json' automatically
// for plain objects, and lets the browser supply the correct multipart boundary
// when the body is a FormData instance.
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Normalizes any thrown error into a stable ApiError shape for the UI.
export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
    return {
      message:
        axiosError.response?.data?.detail ??
        axiosError.response?.data?.message ??
        axiosError.message,
      status: axiosError.response?.status,
      details: axiosError.response?.data,
    };
  }

  return {
    message: error instanceof Error ? error.message : 'Unexpected error',
  };
}

// Only endpoint that exists on the backend today.
export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health/');
  return data;
}

export default api;
