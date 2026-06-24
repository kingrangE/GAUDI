import type { PublicItem } from "../types";

interface ItemChecklistProps {
  items: PublicItem[];
  flagged: string[];
  onToggle: (id: string) => void;
}

/** Controlled list: each item can be flagged (rejected) by the candidate. */
export function ItemChecklist({ items, flagged, onToggle }: ItemChecklistProps) {
  const flaggedSet = new Set(flagged);
  return (
    <ul style={{ listStyle: "none", padding: 0 }}>
      {items.map((item) => {
        const isFlagged = flaggedSet.has(item.id);
        return (
          <li key={item.id} style={{ marginBottom: 8 }}>
            <label style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
              <input
                type="checkbox"
                checked={isFlagged}
                onChange={() => onToggle(item.id)}
                aria-label={`거부: ${item.text}`}
              />
              <span>{item.text}</span>
            </label>
          </li>
        );
      })}
    </ul>
  );
}
