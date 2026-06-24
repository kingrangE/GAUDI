import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "./cn";

type SectionLabelProps = HTMLAttributes<HTMLSpanElement> & {
  /** Render light text for use on a dark ink surface. */
  onDark?: boolean;
  children: ReactNode;
};

/** Small uppercase tracking-wide label ("AGENT OUTPUT", "INSTRUCT THE AGENT"). */
export function SectionLabel({ onDark = false, className, children, ...rest }: SectionLabelProps) {
  return (
    <span
      className={cn(
        "font-mono text-kicker font-medium uppercase tracking-[0.14em]",
        onDark ? "text-ink-label" : "text-ink-faint",
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );
}
