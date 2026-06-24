import type { ReactNode } from "react";

import { cn } from "./cn";

type MetricProps = {
  label: string;
  value: ReactNode;
  /** Optional small text under the value (e.g. "정답 5문제 중"). */
  hint?: ReactNode;
  className?: string;
};

/** Muted label above a large number — test score, precision/recall/F1, etc. */
export function Metric({ label, value, hint, className }: MetricProps) {
  return (
    <div className={cn("rounded-lg border border-line bg-surface px-4 py-3", className)}>
      <div className="font-mono text-kicker uppercase tracking-[0.1em] text-ink-faint">{label}</div>
      <div className="mt-1 font-mono text-2xl font-bold tabular-nums text-ink-900">{value}</div>
      {hint ? <div className="mt-0.5 text-xs text-ink-soft">{hint}</div> : null}
    </div>
  );
}
