import { cn } from "./cn";

type LogoSize = "sm" | "md" | "lg";

const MARK: Record<LogoSize, string> = {
  sm: "h-5 w-5 text-[11px] rounded",
  md: "h-6 w-6 text-xs rounded-md",
  lg: "h-8 w-8 text-sm rounded-md",
};

const WORD: Record<LogoSize, string> = {
  sm: "text-sm tracking-[0.34em]",
  md: "text-base tracking-[0.38em]",
  lg: "text-2xl tracking-[0.4em]",
};

/**
 * GAUDI wordmark — the product logo. Stays in the "judge console" language:
 * a single brand-600 mark + monospace, wide-tracked uppercase letters, with the
 * final letter accented in brand.
 */
export function Logo({
  size = "md",
  className,
}: {
  size?: LogoSize;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <span
        className={cn(
          "grid place-items-center bg-brand-600 font-mono font-bold text-white",
          MARK[size],
        )}
        aria-hidden
      >
        G
      </span>
      <span className={cn("font-mono font-bold leading-none text-ink-900", WORD[size])}>
        GAUD<span className="text-brand-600">I</span>
      </span>
    </span>
  );
}
