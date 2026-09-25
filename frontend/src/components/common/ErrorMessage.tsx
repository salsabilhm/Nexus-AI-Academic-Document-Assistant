import Button from './Button';

interface ErrorMessageProps {
  message: string;
  /** Optional retry handler — rendered as a small secondary button. */
  onRetry?: () => void;
  /** Optional dismiss handler — rendered as a close button. */
  onDismiss?: () => void;
}

// Consistent error block for API and validation errors.
export default function ErrorMessage({ message, onRetry, onDismiss }: ErrorMessageProps) {
  return (
    <div
      role="alert"
      className="flex items-start justify-between gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3"
    >
      <div className="flex items-start gap-2 text-sm text-red-700">
        <svg
          className="mt-0.5 h-4 w-4 shrink-0"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
        </svg>
        <span>{message}</span>
      </div>

      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} className="shrink-0">
          Retry
        </Button>
      )}

      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss error"
          className="shrink-0 rounded-lg p-1 text-red-400 transition-colors hover:bg-red-100 hover:text-red-700"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            className="h-4 w-4"
            aria-hidden="true"
          >
            <path d="M6 6l12 12M18 6 6 18" />
          </svg>
        </button>
      )}
    </div>
  );
}
