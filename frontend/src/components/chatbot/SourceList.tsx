import type { Source } from '../../types/chat';

interface SourceListProps {
  sources: Source[];
}

// ---------------------------------------------------------------------------
// Grouped citation block rendered below an assistant answer.
//
// Chunks of the same logical source (same document + same inner file for a
// ZIP upload) are grouped into one entry with a University/Student badge,
// and repeated passages at the same page/section collapse to one excerpt —
// so 8 retrieved chunks read as a few clear sources, not a repetitive dump.
// Only document/page/section/excerpt are shown: no scores or vector details.
// ---------------------------------------------------------------------------

interface Passage {
  key: string;
  pageNumber?: number;
  section?: string;
  excerpt: string;
}

interface SourceGroup {
  key: string;
  documentType?: 'university' | 'student';
  documentName: string;
  passages: Passage[];
}

/** How many excerpts one source shows before summarizing the rest. */
const MAX_PASSAGES_PER_GROUP = 3;

function groupSources(sources: Source[]): SourceGroup[] {
  const groups: SourceGroup[] = [];
  const byKey = new Map<string, SourceGroup>();

  for (const source of sources) {
    // documentName includes the inner path for ZIP members
    // ("atelier.zip / chapters/contributions.tex"), so different files of
    // one archive stay separate, readable sources.
    const key = `${source.documentId}|${source.documentName}`;
    let group = byKey.get(key);
    if (!group) {
      group = {
        key,
        documentType: source.documentType,
        documentName: source.documentName,
        passages: [],
      };
      byKey.set(key, group);
      groups.push(group);
    }

    // Same page/section (even with overlapping excerpts) = one citation.
    const passageKey = `${source.pageNumber ?? ''}|${source.section ?? ''}`;
    if (!group.passages.some((passage) => passage.key === passageKey)) {
      group.passages.push({
        key: passageKey,
        pageNumber: source.pageNumber,
        section: source.section,
        excerpt: source.excerpt,
      });
    }
  }

  return groups;
}

function locationLine(passage: Passage): string | null {
  const parts: string[] = [];
  if (passage.pageNumber !== undefined) parts.push(`p. ${passage.pageNumber}`);
  if (passage.section) parts.push(`Section: ${passage.section}`);
  return parts.length > 0 ? parts.join(' · ') : null;
}

function TypeBadge({ type }: { type: 'university' | 'student' }) {
  const isUniversity = type === 'university';
  return (
    <span
      className="shrink-0 rounded-md px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider"
      style={
        isUniversity
          ? {
              background: 'rgba(124,58,237,0.18)',
              border: '1px solid rgba(124,58,237,0.4)',
              color: '#c4b5fd',
            }
          : {
              background: 'rgba(16,185,129,0.14)',
              border: '1px solid rgba(16,185,129,0.3)',
              color: '#6ee7b7',
            }
      }
    >
      {isUniversity ? 'University' : 'Student'}
    </span>
  );
}

export default function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) return null;

  const groups = groupSources(sources);

  return (
    <div
      className="mt-3 pt-3"
      style={{ borderTop: '1px solid rgba(192,132,252,0.12)' }}
    >
      <p
        className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-widest"
        style={{ color: '#7c3aed' }}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          className="h-3 w-3"
          aria-hidden="true"
        >
          <path d="M10 13a5 5 0 0 0 7.07 0l2.83-2.83a5 5 0 0 0-7.07-7.07L11.4 4.6" />
          <path d="M14 11a5 5 0 0 0-7.07 7.07L11.4 19.4a5 5 0 0 0 7.07 7.07L14 11" />
        </svg>
        Sources
      </p>

      <ol className="space-y-2">
        {groups.map((group, groupIndex) => (
          <li
            key={group.key}
            className="flex gap-2 rounded-xl px-3 py-2"
            style={{
              background: 'rgba(192,132,252,0.06)',
              border: '1px solid rgba(192,132,252,0.1)',
            }}
          >
            <span
              className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
              style={{ background: 'rgba(192,132,252,0.15)', color: '#c084fc' }}
            >
              {groupIndex + 1}
            </span>

            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-1.5">
                {group.documentType && <TypeBadge type={group.documentType} />}
                <span
                  className="min-w-0 break-all text-xs font-medium"
                  style={{ color: '#e8d5f5' }}
                >
                  {group.documentName}
                </span>
              </div>

              <ul className="mt-1 space-y-1">
                {group.passages.slice(0, MAX_PASSAGES_PER_GROUP).map((passage) => {
                  const location = locationLine(passage);
                  return (
                    <li key={passage.key}>
                      {location && (
                        <p className="text-[11px]" style={{ color: '#6b3fa0' }}>
                          {location}
                        </p>
                      )}
                      <p
                        className="line-clamp-2 text-xs leading-relaxed"
                        style={{ color: '#8b6ab0' }}
                      >
                        {passage.excerpt}
                      </p>
                    </li>
                  );
                })}
                {group.passages.length > MAX_PASSAGES_PER_GROUP && (
                  <li className="text-[11px]" style={{ color: '#6b3fa0' }}>
                    +{group.passages.length - MAX_PASSAGES_PER_GROUP} more passages
                  </li>
                )}
              </ul>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
