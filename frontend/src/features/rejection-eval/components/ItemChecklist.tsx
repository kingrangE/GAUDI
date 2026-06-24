import { Badge } from "@/components/ui/Badge";
import { cn } from "@/components/ui/cn";
import type { PublicItem } from "../types";

interface ItemChecklistProps {
  items: PublicItem[];
  flagged: string[];
  onToggle: (id: string) => void;
}

/** Controlled list (light-on-dark): each item can be flagged (rejected). */
export function ItemChecklist({ items, flagged, onToggle }: ItemChecklistProps) {
  const flaggedSet = new Set(flagged);
  return (
    <ul className="space-y-2">
      {items.map((item) => {
        const isFlagged = flaggedSet.has(item.id);
        return (
          <li key={item.id}>
            <label
              className={cn(
                "flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors",
                isFlagged
                  ? "border-bad-600 bg-bad-600/15"
                  : "border-ink-600 hover:border-ink-muted",
              )}
            >
              <input
                type="checkbox"
                checked={isFlagged}
                onChange={() => onToggle(item.id)}
                aria-label={`거부: ${item.text}`}
                className="mt-0.5 h-4 w-4 accent-bad-600"
              />
              <span className="text-sm leading-relaxed text-ink-text">{item.text}</span>
              {isFlagged ? (
                <Badge tone="bad" className="ml-auto shrink-0">
                  거부
                </Badge>
              ) : null}
            </label>
          </li>
        );
      })}
    </ul>
  );
}
