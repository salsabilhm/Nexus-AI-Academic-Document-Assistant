interface LoadingProps {
  label?: string;
  /** Centers the indicator inside its container. */
  centered?: boolean;
}

// Generic loading indicator (spinner + label).
export default function Loading({ label = 'Loading…', centered = false }: LoadingProps) {
  return (
    <div
      className={`flex items-center gap-2 text-sm text-slate-500 ${centered ? 'justify-center' : ''}`}
      role="status"
      aria-live="polite"
    >
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600" />
      <span>{label}</span>
    </div>
  );
}
