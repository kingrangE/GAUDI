import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "./cn";

type TableProps = HTMLAttributes<HTMLTableElement> & {
  children: ReactNode;
};

/**
 * Judge-console data table. Renders a horizontally-scrollable `<table>` with the
 * shared look: mono uppercase headers, hairline row separators, no border on the
 * last row. Compose with plain `<thead>/<tbody>/<tr>/<th>/<td>` — the cell styles
 * are applied via descendant selectors so call sites stay markup-only.
 */
export function Table({ className, children, ...rest }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table
        className={cn(
          "w-full border-collapse text-left",
          "[&_th]:h-12 [&_th]:whitespace-nowrap [&_th]:border-b [&_th]:border-line [&_th]:px-3",
          "[&_th]:font-mono [&_th]:text-kicker [&_th]:font-semibold [&_th]:uppercase [&_th]:tracking-[0.1em] [&_th]:text-ink-faint",
          "[&_td]:h-[54px] [&_td]:whitespace-nowrap [&_td]:border-b [&_td]:border-line [&_td]:px-3 [&_td]:align-middle [&_td]:text-sm [&_td]:text-ink-soft",
          "[&_tr:last-child_td]:border-b-0",
          className,
        )}
        {...rest}
      >
        {children}
      </table>
    </div>
  );
}
