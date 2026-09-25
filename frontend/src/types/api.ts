// Reusable API response and error shapes shared by all services.

/** Standard error body returned by the API layer. */
export interface ApiError {
  message: string;
  status?: number;
  details?: unknown;
}

/** Envelope used for list endpoints (matches Django REST Framework pagination). */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** Response of GET /api/health/ — the only endpoint that exists today. */
export interface HealthResponse {
  status: string;
  service: string;
}
