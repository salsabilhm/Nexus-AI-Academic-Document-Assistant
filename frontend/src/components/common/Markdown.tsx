import { Fragment, useMemo, type ReactNode } from 'react';

/**
 * Dependency-free Markdown renderer for Nexus answers.
 *
 * Renders the Markdown a chat LLM actually emits — headings, paragraphs,
 * **bold**, *italic*, `inline code`, ~~strikethrough~~, fenced code blocks,
 * links, nested bullet/numbered lists, pipe tables (GFM, with alignment),
 * blockquotes and horizontal rules — as React elements built from parsed
 * text.
 *
 * Nothing is ever injected as HTML (no `dangerouslySetInnerHTML`): every
 * piece of text lands in a text node, so a crafted answer cannot escape its
 * context. Markdown that is not recognised simply stays readable text,
 * never raw syntax pretending to be a heading.
 */

interface MarkdownProps {
  text: string;
  className?: string;
}

// ---------------------------------------------------------------------------
// Inline formatting: **bold**  *italic*  `code`  ~~strike~~  [text](url)
// ---------------------------------------------------------------------------

const INLINE_PATTERN =
  /(\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`|~~[^~\n]+~~|\[[^\]\n]+\]\([^)\s]+\))/g;

const LINK_PATTERN = /^\[([^\]\n]+)\]\(([^)\s]+)\)$/;

function renderInline(text: string, keyBase: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  text.split(INLINE_PATTERN).forEach((part, index) => {
    if (!part) return;
    const key = `${keyBase}-${index}`;

    if (part.length > 4 && part.startsWith('**') && part.endsWith('**')) {
      nodes.push(
        <strong key={key} className="font-semibold" style={{ color: '#f0e4ff' }}>
          {renderInline(part.slice(2, -2), key)}
        </strong>,
      );
      return;
    }
    if (part.length > 2 && part.startsWith('`') && part.endsWith('`')) {
      nodes.push(
        <code
          key={key}
          className="rounded px-1.5 py-0.5 font-mono text-[0.85em]"
          style={{ background: 'rgba(192,132,252,0.12)', color: '#d8b4fe' }}
        >
          {part.slice(1, -1)}
        </code>,
      );
      return;
    }
    if (part.length > 4 && part.startsWith('~~') && part.endsWith('~~')) {
      nodes.push(
        <del key={key} style={{ color: '#8b6ab0' }}>
          {renderInline(part.slice(2, -2), key)}
        </del>,
      );
      return;
    }
    const link = LINK_PATTERN.exec(part);
    if (link && /^https?:\/\//i.test(link[2])) {
      nodes.push(
        <a
          key={key}
          href={link[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
          style={{ color: '#a78bfa' }}
        >
          {renderInline(link[1], key)}
        </a>,
      );
      return;
    }
    if (part.length > 2 && part.startsWith('*') && part.endsWith('*')) {
      nodes.push(
        <em key={key} className="italic">
          {renderInline(part.slice(1, -1), key)}
        </em>,
      );
      return;
    }
    nodes.push(<Fragment key={key}>{part}</Fragment>);
  });
  return nodes;
}

// ---------------------------------------------------------------------------
// Block model
// ---------------------------------------------------------------------------

type ListKind = 'bullet' | 'ordered';

interface ListNode {
  kind: ListKind;
  indent: number;
  text: string;
  children: ListNode[];
}

type Alignment = 'left' | 'center' | 'right';

type Block =
  | { type: 'heading'; depth: number; text: string }
  | { type: 'paragraph'; text: string }
  | { type: 'code'; lang: string; code: string }
  | { type: 'list'; items: ListNode[] }
  | { type: 'table'; header: string[]; align: Alignment[]; rows: string[][] }
  | { type: 'quote'; text: string }
  | { type: 'hr' };

const HEADING_PATTERN = /^(#{1,6})\s+(.*)$/;
const HR_PATTERN = /^\s{0,3}(-{3,}|\*{3,}|_{3,})\s*$/;
const QUOTE_PATTERN = /^\s{0,3}>\s?/;
const LIST_PATTERN = /^(\s*)([-*+]|\d{1,9}[.)])\s+(.*)$/;

function splitRow(row: string): string[] {
  const trimmed = row.trim().replace(/^\|/, '').replace(/\|$/, '');
  return trimmed
    .split(/(?<!\\)\|/)
    .map((cell) => cell.trim().replace(/\\\|/g, '|'));
}

function isTableSeparator(line: string): boolean {
  const trimmed = line.trim();
  return (
    trimmed.includes('|') &&
    trimmed.includes('-') &&
    /^\|?[\s:|-]+\|?$/.test(trimmed)
  );
}

function isBlockStart(lines: string[], index: number): boolean {
  const line = lines[index];
  if (/^\s*```/.test(line)) return true;
  if (HEADING_PATTERN.test(line)) return true;
  if (HR_PATTERN.test(line)) return true;
  if (QUOTE_PATTERN.test(line)) return true;
  return (
    line.includes('|') &&
    index + 1 < lines.length &&
    isTableSeparator(lines[index + 1])
  );
}

function parseAlignment(line: string): Alignment[] {
  return splitRow(line).map((cell) => {
    if (cell.startsWith(':') && cell.endsWith(':')) return 'center';
    if (cell.endsWith(':')) return 'right';
    return 'left';
  });
}

function parseList(lines: string[]): ListNode[] {
  const roots: ListNode[] = [];
  const stack: ListNode[] = [];
  for (const raw of lines) {
    const match = LIST_PATTERN.exec(raw);
    if (!match) {
      // Lazy continuation: an unindented line extends the open item.
      const open = stack[stack.length - 1];
      if (open) open.text = `${open.text} ${raw.trim()}`;
      continue;
    }
    const indent = match[1].replace(/\t/g, '  ').length;
    const node: ListNode = {
      kind: /\d/.test(match[2][0]) ? 'ordered' : 'bullet',
      indent,
      text: match[3],
      children: [],
    };
    while (stack.length > 0 && stack[stack.length - 1].indent >= indent) {
      stack.pop();
    }
    const parent = stack[stack.length - 1];
    if (parent) parent.children.push(node);
    else roots.push(node);
    stack.push(node);
  }
  return roots;
}

function parseBlocks(source: string): Block[] {
  const lines = source.replace(/\r\n?/g, '\n').split('\n');
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i += 1;
      continue;
    }

    // Fenced code block: ```lang ... ```
    const fence = /^\s*```([\w+-]*)/.exec(line);
    if (fence) {
      const lang = fence[1] ?? '';
      const body: string[] = [];
      i += 1;
      while (i < lines.length && !/^\s*```/.test(lines[i])) {
        body.push(lines[i]);
        i += 1;
      }
      i += 1; // closing fence (or end of input)
      blocks.push({ type: 'code', lang, code: body.join('\n') });
      continue;
    }

    // ATX heading: ## Title
    const heading = HEADING_PATTERN.exec(line.trim());
    if (heading) {
      blocks.push({
        type: 'heading',
        depth: heading[1].length,
        text: heading[2].trim(),
      });
      i += 1;
      continue;
    }

    // Horizontal rule: --- | *** | ___
    if (HR_PATTERN.test(line)) {
      blocks.push({ type: 'hr' });
      i += 1;
      continue;
    }

    // Blockquote: > quoted markdown (parsed recursively)
    if (QUOTE_PATTERN.test(line)) {
      const body: string[] = [];
      while (i < lines.length && QUOTE_PATTERN.test(lines[i])) {
        body.push(lines[i].replace(QUOTE_PATTERN, ''));
        i += 1;
      }
      blocks.push({ type: 'quote', text: body.join('\n') });
      continue;
    }

    // Pipe table: header row followed by a |---| separator row
    if (line.includes('|') && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const header = splitRow(line);
      const align = parseAlignment(lines[i + 1]);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim() && lines[i].includes('|')) {
        rows.push(splitRow(lines[i]));
        i += 1;
      }
      blocks.push({ type: 'table', header, align, rows });
      continue;
    }

    // List (bullet or ordered, nesting by indent), with lazy continuations
    if (LIST_PATTERN.test(line)) {
      const listLines: string[] = [];
      while (
        i < lines.length &&
        lines[i].trim() !== '' &&
        (LIST_PATTERN.test(lines[i]) || !isBlockStart(lines, i))
      ) {
        listLines.push(lines[i]);
        i += 1;
      }
      blocks.push({ type: 'list', items: parseList(listLines) });
      continue;
    }

    // Paragraph: consecutive plain lines until a blank line or new block
    const paragraph: string[] = [line.trim()];
    i += 1;
    while (i < lines.length && lines[i].trim() !== '' && !isBlockStart(lines, i)) {
      paragraph.push(lines[i].trim());
      i += 1;
    }
    blocks.push({ type: 'paragraph', text: paragraph.join(' ') });
  }

  return blocks;
}

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------

const HEADING_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] as const;
const HEADING_SIZES = ['text-xl', 'text-lg', 'text-base', 'text-sm', 'text-sm', 'text-sm'];

function renderListNodes(nodes: ListNode[], keyBase: string, topLevel: boolean): ReactNode {
  if (nodes.length === 0) return null;
  const ordered = nodes[0].kind === 'ordered';
  const Tag = ordered ? 'ol' : 'ul';
  return (
    <Tag
      className={`${topLevel ? 'my-2' : 'mt-1.5'} space-y-1 ${
        ordered ? 'list-decimal' : 'list-disc'
      } pl-5 marker:text-[#7c3aed]`}
    >
      {nodes.map((node, index) => {
        const key = `${keyBase}-${index}`;
        return (
          <li key={key} className="leading-relaxed" style={{ color: '#e8d5f5' }}>
            {renderInline(node.text, key)}
            {node.children.length > 0 &&
              renderListNodes(node.children, `${key}-nested`, false)}
          </li>
        );
      })}
    </Tag>
  );
}

function renderBlocks(blocks: Block[], keyBase: string): ReactNode[] {
  return blocks.map((block, index) => {
    const key = `${keyBase}${index}`;
    const spacing = index === 0 ? 'mt-0' : 'mt-4';

    switch (block.type) {
      case 'heading': {
        const depth = Math.min(block.depth, 6) - 1;
        const Tag = HEADING_TAGS[depth];
        return (
          <Tag
            key={key}
            className={`${spacing} mb-2 ${HEADING_SIZES[depth]} font-semibold`}
            style={{ color: '#f0e4ff' }}
          >
            {renderInline(block.text, key)}
          </Tag>
        );
      }

      case 'paragraph':
        return (
          <p key={key} className="my-2 leading-relaxed first:mt-0">
            {renderInline(block.text, key)}
          </p>
        );

      case 'code':
        return (
          <pre
            key={key}
            className="my-3 overflow-x-auto rounded-xl p-3 text-xs leading-relaxed"
            style={{
              background: 'rgba(6,4,14,0.75)',
              border: '1px solid rgba(192,132,252,0.14)',
            }}
          >
            {block.lang && (
              <span
                className="mb-1 block text-[10px] font-semibold uppercase tracking-wider"
                style={{ color: '#6b3fa0' }}
              >
                {block.lang}
              </span>
            )}
            <code className="font-mono" style={{ color: '#e8d5f5' }}>
              {block.code}
            </code>
          </pre>
        );

      case 'list':
        return <Fragment key={key}>{renderListNodes(block.items, key, true)}</Fragment>;

      case 'table':
        return (
          <div
            key={key}
            className="my-3 overflow-x-auto rounded-xl"
            style={{
              border: '1px solid rgba(192,132,252,0.16)',
              background: 'rgba(255,255,255,0.02)',
            }}
          >
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr style={{ background: 'rgba(192,132,252,0.08)' }}>
                  {block.header.map((cell, cellIndex) => (
                    <th
                      key={cellIndex}
                      className="px-3 py-2 text-left font-semibold"
                      style={{
                        color: '#f0e4ff',
                        borderBottom: '1px solid rgba(192,132,252,0.2)',
                        textAlign: block.align[cellIndex] ?? 'left',
                      }}
                    >
                      {renderInline(cell, `${key}-h${cellIndex}`)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {block.rows.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    style={
                      rowIndex % 2 === 1
                        ? { background: 'rgba(255,255,255,0.02)' }
                        : undefined
                    }
                  >
                    {row.map((cell, cellIndex) => (
                      <td
                        key={cellIndex}
                        className="px-3 py-1.5 align-top"
                        style={{
                          color: '#e8d5f5',
                          borderBottom: '1px solid rgba(192,132,252,0.1)',
                          textAlign: block.align[cellIndex] ?? 'left',
                        }}
                      >
                        {renderInline(cell, `${key}-c${rowIndex}-${cellIndex}`)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case 'quote':
        return (
          <blockquote
            key={key}
            className="my-3 rounded-r-xl border-l-2 py-1 pl-3"
            style={{
              borderColor: 'rgba(192,132,252,0.45)',
              background: 'rgba(192,132,252,0.05)',
            }}
          >
            {renderBlocks(parseBlocks(block.text), `${key}-q`)}
          </blockquote>
        );

      case 'hr':
        return (
          <hr
            key={key}
            className="my-4 border-0"
            style={{ borderTop: '1px solid rgba(192,132,252,0.15)' }}
          />
        );

      default:
        return null;
    }
  });
}

export default function Markdown({ text, className }: MarkdownProps) {
  const blocks = useMemo(() => parseBlocks(text ?? ''), [text]);
  return (
    <div className={className} style={{ color: '#e8d5f5' }}>
      {renderBlocks(blocks, 'md-')}
    </div>
  );
}
