import { cn } from "./cn";

export type TabItem = {
  id: string;
  label: string;
};

type TabsProps = {
  tabs: TabItem[];
  active: string;
  onChange: (id: string) => void;
  className?: string;
};

/** Simple tab strip for panel headers (mockup's "PROMPT GUIDE" / problem name). */
export function Tabs({ tabs, active, onChange, className }: TabsProps) {
  return (
    <div role="tablist" className={cn("flex items-center gap-1", className)}>
      {tabs.map((tab) => {
        const selected = tab.id === active;
        return (
          <button
            key={tab.id}
            role="tab"
            type="button"
            aria-selected={selected}
            onClick={() => onChange(tab.id)}
            className={cn(
              "rounded-md px-3 py-1.5 text-xs font-semibold transition-colors",
              selected
                ? "bg-brand-50 text-brand-700"
                : "text-slate-500 hover:bg-slate-100 hover:text-slate-700",
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
