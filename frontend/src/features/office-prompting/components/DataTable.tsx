import { cn } from "@/components/ui/cn";

type DataTableProps = {
  columns: string[];
  rows: Record<string, unknown>[];
  /** Render for the dark ink well (AI result) instead of a light card. */
  onDark?: boolean;
  maxHeightClass?: string;
};

/** Compact scrollable table used for both the reference datasets (light) and
 *  the AI's returned rows (on the dark ink well). */
export function DataTable({
  columns,
  rows,
  onDark = false,
  maxHeightClass = "max-h-72",
}: DataTableProps) {
  return (
    <div className={cn("overflow-auto rounded-md", maxHeightClass)}>
      <table className="w-full border-collapse text-left font-mono text-xs tabular-nums">
        <thead className="sticky top-0">
          <tr className={onDark ? "bg-ink-800" : "bg-paper"}>
            {columns.map((c) => (
              <th
                key={c}
                className={cn(
                  "whitespace-nowrap px-2 py-1.5 font-medium uppercase tracking-[0.08em]",
                  onDark ? "text-ink-muted" : "text-ink-faint",
                )}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className={cn(
                "border-t",
                onDark ? "border-ink-700 text-ink-text" : "border-line text-ink-900",
              )}
            >
              {columns.map((c) => (
                <td key={c} className="whitespace-nowrap px-2 py-1">
                  {String(row[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
