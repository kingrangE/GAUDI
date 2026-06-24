import { cn } from "@/components/ui";

export type StepScore = {
  key: string;
  label: string;
  /** null = step not yet attempted */
  score: number | null;
};

type CandidateStepBarsProps = {
  steps: StepScore[];
  className?: string;
};

/**
 * Five mini progress bars — one per exam step — for the candidate card in the admin
 * dashboard. Labels are short monospace kickers (CTX / SPEC / REJ / TEST / DEV).
 * Missing scores render as a ghost bar with "—".
 */
export function CandidateStepBars({ steps, className }: CandidateStepBarsProps) {
  return (
    <div className={cn("grid gap-1.5", className)} aria-label="단계별 점수">
      {steps.map((step) => {
        const pct = step.score ?? 0;
        const hasScore = step.score !== null;
        return (
          <div
            key={step.key}
            className="grid grid-cols-[36px_minmax(0,1fr)_28px] items-center gap-2"
          >
            <span className="font-mono text-kicker uppercase tracking-[0.12em] text-ink-faint">
              {step.label}
            </span>
            <div className="h-1.5 overflow-hidden rounded-full bg-paper">
              <div
                className={cn(
                  "h-full rounded-full",
                  hasScore
                    ? pct >= 70
                      ? "bg-good-600"
                      : pct >= 40
                        ? "bg-brand-600"
                        : "bg-bad-600"
                    : "bg-line",
                )}
                style={{ width: `${pct}%` }}
                role="presentation"
              />
            </div>
            <span className="text-right font-mono text-kicker tabular-nums text-ink-soft">
              {hasScore ? String(Math.round(step.score!)) : "—"}
            </span>
          </div>
        );
      })}
    </div>
  );
}
