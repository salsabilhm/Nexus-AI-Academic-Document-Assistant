import { useRef, useState } from 'react';
import type { ChangeEvent, DragEvent, KeyboardEvent } from 'react';

interface DocumentUploadProps {
  onFileSelected?: (file: File) => void;
  /** Compact variant used inside the chatbot side panel. */
  compact?: boolean;
  /** Secondary line below the label. */
  hint?: string;
}

// Drag & drop / click upload area.
// UI only: the selected file is handed to the parent. Once the backend exposes
// a document endpoint, the parent will call documentApi.uploadDocument().
export default function DocumentUpload({
  onFileSelected,
  compact = false,
  hint = 'University requirements, guidelines, templates or your own research.',
}: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file: File | undefined) => {
    if (file) onFileSelected?.(file);
  };

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFile(event.target.files?.[0]);
    // Allow selecting the same file again later.
    event.target.value = '';
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    handleFile(event.dataTransfer.files?.[0]);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      inputRef.current?.click();
    }
  };

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onKeyDown={handleKeyDown}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      role="button"
      tabIndex={0}
      aria-label="Upload a document"
      className={`group flex w-full cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed text-center transition-colors ${
        compact ? 'gap-1.5 px-4 py-6' : 'gap-2 px-6 py-10'
      } ${
        isDragging
          ? 'border-indigo-400 bg-indigo-50'
          : 'border-slate-300 bg-white hover:border-indigo-300 hover:bg-indigo-50/40'
      }`}
    >
      <span
        className={`flex items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 transition-colors group-hover:bg-indigo-100 ${
          compact ? 'h-8 w-8' : 'h-11 w-11'
        }`}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={compact ? 'h-4 w-4' : 'h-5 w-5'}
          aria-hidden="true"
        >
          <path d="M12 16V4M12 4 7 9M12 4l5 5" />
          <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
        </svg>
      </span>

      <p className={compact ? 'text-xs font-medium text-slate-700' : 'text-sm font-medium text-slate-700'}>
        Drop a file here or click to browse
      </p>
      {!compact && <p className="max-w-sm text-xs text-slate-500">{hint}</p>}
      <p className="text-[11px] text-slate-400">PDF · DOCX · TXT · MD</p>

      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.doc,.txt,.md"
        onChange={handleChange}
      />
    </div>
  );
}
