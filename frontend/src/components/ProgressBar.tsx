export function ProgressBar({
  current, total, indeterminate = false, maxPercent = 100, label = "진행",
}: {
  current: number; total: number; indeterminate?: boolean; maxPercent?: number; label?: string;
}) {
  const safeTotal = Number.isFinite(total) ? Math.max(0, total) : 0;
  const safeCurrent = Number.isFinite(current) ? Math.max(0, Math.min(current, safeTotal)) : 0;
  const pct = safeTotal > 0 ? Math.min(Math.max(0, maxPercent), Math.round(safeCurrent / safeTotal * 100)) : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-xs font-medium text-ink-soft">
        <span>{indeterminate ? label : `${label} ${safeCurrent} / ${safeTotal}`}</span>
        <span>{indeterminate ? "진행 중" : `${pct}%`}</span>
      </div>
      <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-line" role="progressbar"
        aria-label={label} aria-valuemin={0} aria-valuemax={100}
        aria-valuenow={indeterminate ? undefined : pct}
        aria-valuetext={indeterminate ? "완료 단위를 기다리고 있습니다" : `${pct}%`}>
        <div className={`h-full rounded-full bg-brand-600 ${indeterminate ? "w-1/3 motion-safe:animate-pulse" : "transition-all"}`}
          style={indeterminate ? undefined : { width: `${pct}%` }} />
      </div>
    </div>
  );
}
