import { useRef, useState } from 'react';
import type { ChangeEvent, DragEvent, KeyboardEvent } from 'react';
import type { DocumentSource } from '../../types/document';

// ------------------------------------------------------------------ //
// Types                                                                //
// ------------------------------------------------------------------ //

interface DocumentUploadProps {
  /** Called once a valid file + source are confirmed.
   *  May return a Promise (e.g. the real API call) — the component awaits it
   *  and reflects loading/error state from the settled result. */
  onFileSelected?: (file: File, source: DocumentSource) => void | Promise<unknown>;
  /** Compact variant used inside the chatbot sidebar. */
  compact?: boolean;
}

// ------------------------------------------------------------------ //
// Supported file types — must match ALLOWED_EXTENSIONS in            //
// backend/chatbot/api/serializers.py (the server has the final say). //
// ------------------------------------------------------------------ //
const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.zip'];

const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/zip',
  'application/x-zip-compressed',
];

/** Everything the file input should offer in the picker. */
const FILE_ACCEPT = [...ALLOWED_EXTENSIONS, ...ALLOWED_MIME_TYPES].join(',');

/** Short label shown in hints and captions. */
const SUPPORTED_LABEL = 'PDF, DOC, DOCX, ZIP';

type UploadState = 'idle' | 'ready' | 'uploading' | 'success' | 'error';

interface SourceOption {
  value: DocumentSource;
  label: string;
  description: string;
  icon: React.ReactNode;
}

// ------------------------------------------------------------------ //
// Source option definitions                                            //
// ------------------------------------------------------------------ //
const SOURCE_OPTIONS: SourceOption[] = [
  {
    value: 'university',
    label: 'University',
    description: 'Official university requirements, guidelines, templates, or regulations.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7}
        strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    value: 'student',
    label: 'Student',
    description: 'Your thesis, research paper, report, or academic work.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7}
        strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
        <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
        <path d="M6 12v5c3 3 9 3 12 0v-5" />
      </svg>
    ),
  },
];

// ------------------------------------------------------------------ //
// Component                                                            //
// ------------------------------------------------------------------ //
export default function DocumentUpload({ onFileSelected, compact = false }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const [source, setSource] = useState<DocumentSource | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // ---------- helpers ----------

  // Mirrors the backend rule: the extension gates the file, and a file with
  // no extension is accepted only when its MIME type is one we recognise.
  const isAllowedFile = (f: File) => {
    const dot = f.name.lastIndexOf('.');
    const ext = dot >= 0 ? f.name.slice(dot).toLowerCase() : '';
    if (ALLOWED_EXTENSIONS.includes(ext)) return true;
    return ext === '' && ALLOWED_MIME_TYPES.includes(f.type);
  };

  /** Uppercase extension used in the "12 KB · PDF" caption. */
  const fileKind = (f: File) => {
    const dot = f.name.lastIndexOf('.');
    return dot >= 0 ? f.name.slice(dot + 1).toUpperCase() : 'FILE';
  };

  const applyFile = (f: File | undefined) => {
    if (!f) return;
    if (!isAllowedFile(f)) {
      setErrorMsg(`Only ${SUPPORTED_LABEL} files are accepted. Please choose a supported file.`);
      setFile(null);
      setUploadState('error');
      return;
    }
    setErrorMsg(null);
    setFile(f);
    setUploadState('ready');
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    applyFile(e.target.files?.[0]);
    e.target.value = '';
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    applyFile(e.dataTransfer.files?.[0]);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inputRef.current?.click(); }
  };

  const handleConfirm = async () => {
    if (!file || !source) return;
    setUploadState('uploading');
    setErrorMsg(null);
    try {
      await onFileSelected?.(file, source);
      setUploadState('success');
      // Reset after showing success so the user can upload another file
      setTimeout(() => {
        setFile(null);
        setSource(null);
        setUploadState('idle');
        setErrorMsg(null);
      }, 2000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed. Please try again.';
      setErrorMsg(msg);
      setUploadState('error');
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadState('idle');
    setErrorMsg(null);
  };

  const isUploading = uploadState === 'uploading';
  const canConfirm = !!file && !!source && uploadState === 'ready';

  // ------------------------------------------------------------------ //
  // Compact variant (chatbot sidebar)                                   //
  // ------------------------------------------------------------------ //
  if (compact) {
    return (
      <div className="space-y-2">
        {/* Source selector — two small pills */}
        <div className="flex gap-1.5">
          {SOURCE_OPTIONS.map((opt) => {
            const active = source === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => setSource(opt.value)}
                className="flex flex-1 items-center justify-center gap-1.5 rounded-xl px-2 py-2 text-xs font-medium transition-all"
                style={{
                  background: active ? 'rgba(192,132,252,0.18)' : 'rgba(255,255,255,0.03)',
                  border: active ? '1px solid rgba(192,132,252,0.5)' : '1px solid rgba(192,132,252,0.12)',
                  color: active ? '#c084fc' : '#6b3fa0',
                }}
              >
                {opt.icon}
                {opt.label}
              </button>
            );
          })}
        </div>

        {/* Drop zone */}
        <div
          onClick={() => inputRef.current?.click()}
          onKeyDown={handleKeyDown}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
          aria-label="Upload a document"
          className="flex w-full cursor-pointer flex-col items-center justify-center gap-1.5 rounded-2xl border-2 border-dashed px-4 py-4 text-center transition-all duration-200"
          style={{
            borderColor: isDragging ? 'rgba(192,132,252,0.6)' : file ? 'rgba(192,132,252,0.45)' : 'rgba(192,132,252,0.2)',
            background: isDragging ? 'rgba(192,132,252,0.08)' : file ? 'rgba(192,132,252,0.05)' : 'rgba(255,255,255,0.02)',
          }}
        >
          {file ? (
            <>
              <span className="flex h-7 w-7 items-center justify-center rounded-lg"
                style={{ background: 'rgba(192,132,252,0.12)', color: '#c084fc' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
                  strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5" aria-hidden="true">
                  <path d="M14 3v5h5" />
                  <path d="M19 8v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5z" />
                </svg>
              </span>
              <p className="max-w-full truncate text-[11px] font-medium" style={{ color: '#e8d5f5' }}>
                {file.name}
              </p>
            </>
          ) : (
            <>
              <span className="flex h-7 w-7 items-center justify-center rounded-lg"
                style={{ background: 'rgba(192,132,252,0.1)', color: '#c084fc' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
                  strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5" aria-hidden="true">
                  <path d="M12 16V4M12 4 7 9M12 4l5 5" />
                  <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
                </svg>
              </span>
              <p className="text-xs font-medium" style={{ color: '#e8d5f5' }}>Upload document</p>
              <p className="text-[10px]" style={{ color: 'rgba(192,132,252,0.4)' }}>{SUPPORTED_LABEL}</p>
            </>
          )}
        </div>

        {/* Error */}
        {errorMsg && (
          <p className="text-[11px]" style={{ color: '#f87171' }}>{errorMsg}</p>
        )}

        {/* Confirm */}
        <button
          type="button"
          onClick={handleConfirm}
          disabled={!canConfirm || isUploading}
          className="w-full rounded-xl py-2 text-xs font-semibold transition-all disabled:cursor-not-allowed disabled:opacity-40"
          style={{
            background: canConfirm || isUploading ? 'linear-gradient(135deg,#c084fc,#7c3aed)' : 'rgba(192,132,252,0.1)',
            color: canConfirm || isUploading ? '#0d0014' : '#6b3fa0',
          }}
        >
          {isUploading ? 'Uploading…' : uploadState === 'success' ? '✓ Added' : 'Add document'}
        </button>

        <input ref={inputRef} type="file" className="hidden" accept={FILE_ACCEPT} onChange={handleChange} />
      </div>
    );
  }

  // ------------------------------------------------------------------ //
  // Full variant (home page / standalone)                               //
  // ------------------------------------------------------------------ //
  return (
    <div
      className="w-full rounded-2xl p-6"
      style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(192,132,252,0.14)' }}
    >
      {/* Title */}
      <p className="mb-4 text-sm font-semibold" style={{ color: '#f0e4ff' }}>
        Upload a document
      </p>

      {/* Source selector */}
      <div className="mb-5">
        <p className="mb-2.5 text-xs font-medium" style={{ color: '#a78bca' }}>
          What type of document is this?
        </p>
        <div className="grid grid-cols-2 gap-3">
          {SOURCE_OPTIONS.map((opt) => {
            const active = source === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => setSource(opt.value)}
                className="flex flex-col items-start gap-1.5 rounded-xl p-3.5 text-left transition-all duration-150"
                style={{
                  background: active ? 'rgba(192,132,252,0.12)' : 'rgba(255,255,255,0.03)',
                  border: active ? '1.5px solid rgba(192,132,252,0.55)' : '1.5px solid rgba(192,132,252,0.1)',
                  boxShadow: active ? '0 0 0 3px rgba(192,132,252,0.08)' : 'none',
                }}
              >
                <span
                  className="flex h-8 w-8 items-center justify-center rounded-lg"
                  style={{
                    background: active ? 'rgba(192,132,252,0.18)' : 'rgba(192,132,252,0.08)',
                    color: active ? '#c084fc' : '#7c3aed',
                  }}
                >
                  {opt.icon}
                </span>
                <span className="text-xs font-semibold" style={{ color: active ? '#f0e4ff' : '#a78bca' }}>
                  {opt.label}
                </span>
                <span className="text-[11px] leading-relaxed" style={{ color: active ? '#8b6ab0' : '#4a2870' }}>
                  {opt.description}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        onKeyDown={handleKeyDown}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        aria-label="Upload a document"
        className="flex w-full cursor-pointer flex-col items-center justify-center gap-2.5 rounded-2xl border-2 border-dashed px-6 py-8 text-center transition-all duration-200"
        style={{
          borderColor: isDragging
            ? 'rgba(192,132,252,0.65)'
            : file
            ? 'rgba(192,132,252,0.5)'
            : 'rgba(192,132,252,0.2)',
          background: isDragging
            ? 'rgba(192,132,252,0.08)'
            : file
            ? 'rgba(192,132,252,0.05)'
            : 'rgba(255,255,255,0.02)',
        }}
        onMouseEnter={(e) => {
          if (!isDragging && !file)
            (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(192,132,252,0.38)';
        }}
        onMouseLeave={(e) => {
          if (!isDragging && !file)
            (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(192,132,252,0.2)';
        }}
      >
        {file ? (
          /* File selected state */
          <>
            <span className="flex h-11 w-11 items-center justify-center rounded-xl"
              style={{ background: 'rgba(192,132,252,0.12)', color: '#c084fc' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
                strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
                <path d="M14 3v5h5" />
                <path d="M19 8v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5z" />
                <path d="M9 13h6M9 17h4" />
              </svg>
            </span>
            <div>
              <p className="text-sm font-medium" style={{ color: '#e8d5f5' }}>{file.name}</p>
              <p className="mt-0.5 text-xs" style={{ color: '#6b3fa0' }}>
                {(file.size / 1024).toFixed(0)} KB · {fileKind(file)}
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); handleReset(); }}
              className="text-xs transition-all"
              style={{ color: '#7c3aed' }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = '#c084fc'; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = '#7c3aed'; }}
            >
              Remove
            </button>
          </>
        ) : (
          /* Empty drop zone */
          <>
            <span className="flex h-11 w-11 items-center justify-center rounded-xl"
              style={{ background: 'rgba(192,132,252,0.1)', color: '#c084fc' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
                strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
                <path d="M12 16V4M12 4 7 9M12 4l5 5" />
                <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
              </svg>
            </span>
            <p className="text-sm font-medium" style={{ color: '#e8d5f5' }}>
              Drop a file here or click to browse
            </p>
            <p className="text-xs" style={{ color: 'rgba(192,132,252,0.4)' }}>{SUPPORTED_LABEL}</p>
          </>
        )}
      </div>

      {/* Validation / error feedback */}
      {errorMsg && (
        <div
          className="mt-3 flex items-start gap-2 rounded-xl px-3 py-2.5 text-xs"
          style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5' }}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
            strokeLinecap="round" className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true">
            <circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" />
          </svg>
          {errorMsg}
        </div>
      )}

      {/* Missing-selection hint */}
      {!errorMsg && file && !source && (
        <p className="mt-3 text-xs" style={{ color: '#a78bca' }}>
          ↑ Select a document type above before uploading.
        </p>
      )}
      {!errorMsg && source && !file && (
        <p className="mt-3 text-xs" style={{ color: '#a78bca' }}>
          ↑ Choose a file to continue.
        </p>
      )}

      {/* Success feedback */}
      {uploadState === 'success' && (
        <div
          className="mt-3 flex items-center gap-2 rounded-xl px-3 py-2.5 text-xs font-medium"
          style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', color: '#6ee7b7' }}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2}
            strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5" aria-hidden="true">
            <path d="m5 13 4 4L19 7" />
          </svg>
          Document added successfully.
        </div>
      )}

      {/* Upload / confirm button */}
      {uploadState !== 'success' && (
        <button
          type="button"
          onClick={handleConfirm}
          disabled={!canConfirm || isUploading}
          className="mt-4 w-full rounded-xl py-2.5 text-sm font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40"
          style={{
            background: canConfirm || isUploading
              ? 'linear-gradient(135deg,#c084fc 0%,#7c3aed 100%)'
              : 'rgba(192,132,252,0.08)',
            color: canConfirm || isUploading ? '#0d0014' : '#6b3fa0',
            boxShadow: canConfirm || isUploading ? '0 4px 16px rgba(192,132,252,0.25)' : 'none',
          }}
        >
          {isUploading ? 'Uploading…' : 'Upload document'}
        </button>
      )}

      <input ref={inputRef} type="file" className="hidden" accept={FILE_ACCEPT} onChange={handleChange} />
    </div>
  );
}
