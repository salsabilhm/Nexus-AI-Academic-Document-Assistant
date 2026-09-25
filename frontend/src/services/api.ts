import axios from 'axios';
import type { AxiosError } from 'axios';
import type { ApiError, HealthResponse } from '../types/api';

// Central Axios client. Every service (documentApi, chatbotApi) builds on this
// instance so the base URL, headers and error handling live in one place.
// The base URL comes from the environment: never hardcode it here.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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
