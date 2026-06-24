// Split a generated sample into prose + fenced code blocks so the UI can render code
// in a proper code well instead of one flat <pre>.

export type ContentSegment =
  | { kind: "text"; text: string }
  | { kind: "code"; lang: string; code: string };

export function parseContentSegments(content: string): ContentSegment[] {
  const fence = /```[ \t]*([\w+#.-]*)[ \t]*\r?\n([\s\S]*?)```/g;
  const segments: ContentSegment[] = [];
  let last = 0;
  let match: RegExpExecArray | null;

  while ((match = fence.exec(content)) !== null) {
    const before = content.slice(last, match.index).trim();
    if (before) segments.push({ kind: "text", text: before });
    segments.push({ kind: "code", lang: match[1] || "", code: match[2].replace(/\n$/, "") });
    last = match.index + match[0].length;
  }

  const tail = content.slice(last).trim();
  if (tail) segments.push({ kind: "text", text: tail });

  if (segments.length === 0 && content.trim()) {
    segments.push({ kind: "text", text: content.trim() });
  }
  return segments;
}
