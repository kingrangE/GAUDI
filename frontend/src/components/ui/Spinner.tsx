import { cn } from "./cn";

type SpinnerProps = {
  className?: string;
  /** Accessible label announced to screen readers. */
  label?: string;
};

/** Indeterminate circular progress indicator (judge-console accent). */
export function Spinner({ className, label = "로딩 중" }: SpinnerProps) {
  return (
    <span
      role="status"
      aria-label={label}
      className={cn(
        "inline-block h-8 w-8 animate-spin rounded-full border-2 border-line border-t-brand-600",
        className,
      )}
    />
  );
}
