import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "./cn";

type Variant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  children: ReactNode;
};

const BASE = cn(
  "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold",
  "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
  "disabled:cursor-not-allowed",
);

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-brand-600 text-white hover:bg-brand-700 focus-visible:ring-brand-600 disabled:bg-brand-200",
  secondary:
    "border border-line bg-surface text-ink-soft hover:bg-paper focus-visible:ring-brand-300 disabled:text-ink-faint",
  ghost:
    "text-ink-soft hover:bg-paper focus-visible:ring-brand-300 disabled:text-ink-faint",
};

/**
 * Button styling as a class string — apply the button look to a non-button element
 * (e.g. a Next.js <Link> used for navigation) without duplicating the variant classes.
 */
export function buttonClasses(variant: Variant = "primary", className?: string) {
  return cn(BASE, VARIANTS[variant], className);
}

export function Button({ variant = "primary", className, children, ...rest }: ButtonProps) {
  return (
    <button className={buttonClasses(variant, className)} {...rest}>
      {children}
    </button>
  );
}
