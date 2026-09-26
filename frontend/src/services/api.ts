import axios from 'axios';
import type { AxiosError } from 'axios';
import type { ApiError, HealthResponse } from '../types/api';

// ---------------------------------------------------------------------------
// Base URL validation
// ---------------------------------------------------------------------------
// VITE_API_BASE_URL must be set in frontend/.env (copy from .env.example).
// If it is missing, every request silently targets the Vite dev-server origin
// instead of Django, producing 404s that look like routing bugs.
const rawBase: string = import.meta.env.VITE_API_BASE_URL ?? '';

if (!rawBase) {
  // Surface the misconfiguration immediately in the browser console.
  console.error(
    '[Nexus] VITE_API_BASE_URL is not set.\n' +
    'Create frontend/.env and add:\n' +
    '  VITE_API_BASE_URL=http://localhost:8000/api\n' +
    'Then restart the Vite dev server.',
  );
}

// Strip any accidental trailing slash so paths like "/documents/upload/" work
// correctly regardless of how the env var is written.
const API_BASE_URL = rawBase.replace(/\/+$/, '');

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
