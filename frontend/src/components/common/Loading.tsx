interface LoadingProps {
  label?: string;
  centered?: boolean;
}

export default function Loading({ label = 'Loading…', centered = false }: LoadingProps) {
  return (
    <div
      className={`flex items-center gap-2.5 text-sm ${centered ? 'justify-center' : ''}`}
      style={{ color: '#a78bca' }}
      role="status"
      aria-live="polite"
    >
      {/* Tri-dot typing indicator */}
      <span className="flex items-center gap-1" aria-hidden="true">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="h-1.5 w-1.5 rounded-full animate-bounce"
            style={{
              background: '#c084fc',
              animationDelay: `${delay}ms`,
              animationDuration: '1.2s',
            }}
          />
        ))}
      </span>
      <span className="text-xs">{label}</span>
    </div>
  );
}
