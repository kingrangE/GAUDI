import { cn } from "./cn";

type ChipsProps = {
  items: string[];
  /** good = strengths (emerald), bad = weaknesses (amber). */
  tone?: "good" | "warn";
  className?: string;
};

/** Keyword chips for strengths / weaknesses. */
export function Chips({ items, tone = "good", className }: ChipsProps) {
  if (items.length === 0) return null;
  return (
    <div className={cn("flex flex-wrap gap-1.5", className)}>
      {items.map((item, i) => (
        <span
          key={`${item}-${i}`}
          className={cn(
            "rounded-md px-2 py-0.5 text-xs font-medium",
            tone === "good"
              ? "bg-good-50 text-good-700"
              : "bg-amber-50 text-amber-700",
          )}
        >
          {item}
        </span>
      ))}
    </div>
  );
}
