import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "./cn";

type PanelProps = HTMLAttributes<HTMLDivElement> & {
  /** "light" = white content card, "dark" = ink code/output surface. */
  tone?: "light" | "dark";
  /** Remove inner padding (e.g. when wrapping a full-bleed code editor). */
  flush?: boolean;
  children: ReactNode;
};

export function Panel({
  tone = "light",
  flush = false,
  className,
  children,
  ...rest
}: PanelProps) {
  return (
    <div
      className={cn(
        "rounded-lg border",
        flush ? "" : "p-5",
        tone === "dark"
          ? "code-surface border-ink-700"
          : "border-line bg-surface shadow-panel",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
