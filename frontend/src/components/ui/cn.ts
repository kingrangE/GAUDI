/** Join truthy class names. Tiny clsx replacement — no dependency needed. */
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}
