import { Badge } from "@/components/ui";

import type { ResponseType } from "../types";

const META: Record<
  ResponseType,
  { tone: "good" | "warn" | "bad" | "neutral"; label: string }
> = {
  correct: { tone: "good", label: "정확" },
  partial: { tone: "warn", label: "부분" },
  honest_unknown: { tone: "neutral", label: "솔직한 모름" },
  bluff_wrong: { tone: "bad", label: "허세-오답" },
};

/** Coloured badge for an answer's response type (the README rubric buckets). */
export function ResponseTypeBadge({ type }: { type: ResponseType | null }) {
  if (!type) return null;
  const { tone, label } = META[type];
  return <Badge tone={tone}>{label}</Badge>;
}
