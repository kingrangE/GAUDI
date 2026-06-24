import type { ReactNode } from "react";

import { cn } from "./cn";
import { SectionLabel } from "./SectionLabel";

type CodePanelProps = {
  /** Uppercase section label on the left of the header ("AGENT OUTPUT"). */
  label: string;
  /** Optional right-side meta tags (language, turn, etc.). */
  meta?: ReactNode;
  /** When set, the body is rendered as a <pre> with this text. */
  code?: string;
  /** Custom body (e.g. a CodeMirror editor or a checklist). Overrides `code`. */
  children?: ReactNode;
  className?: string;
  /** Drop body padding (for a full-bleed editor). */
  flushBody?: boolean;
};

/** Dark ink panel with a header row — code, agent output, code-under-review. */
export function CodePanel({
  label,
  meta,
  code,
  children,
  className,
  flushBody = false,
}: CodePanelProps) {
  return (
    <div
      className={cn(
        "code-surface flex min-h-0 flex-col overflow-hidden rounded-xl border border-ink-600",
        className,
      )}
    >
      <div className="flex items-center justify-between border-b border-ink-600 px-4 py-2.5">
        <SectionLabel onDark>{label}</SectionLabel>
        {meta ? <div className="flex items-center gap-2">{meta}</div> : null}
      </div>
      <div className={cn("min-h-0 flex-1 overflow-auto", flushBody ? "" : "p-4")}>
        {children ?? (
          <pre className="m-0 whitespace-pre-wrap break-words font-mono text-[13px] leading-relaxed">
            {code}
          </pre>
        )}
      </div>
    </div>
  );
}

/** Small dark meta tag for the CodePanel header (e.g. "python", "TURN 3"). */
export function CodeMeta({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-md border border-ink-600 bg-ink-700 px-2 py-0.5 font-mono text-[11px] text-ink-muted">
      {children}
    </span>
  );
}
