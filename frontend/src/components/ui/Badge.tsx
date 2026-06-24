import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "./cn";

type Tone = "neutral" | "good" | "bad" | "brand" | "warn";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: Tone;
  children: ReactNode;
};

const TONES: Record<Tone, string> = {
  neutral: "border-line bg-paper text-ink-soft",
  good: "border-good-100 bg-good-50 text-good-700",
  bad: "border-bad-100 bg-bad-50 text-bad-700",
  brand: "border-brand-100 bg-brand-50 text-brand-700",
  warn: "border-warn-100 bg-warn-50 text-warn-700",
};

/** Pill badge for difficulty, pass/fail, outcomes, percentages and grades. */
export function Badge({ tone = "neutral", className, children, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        TONES[tone],
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );
}
