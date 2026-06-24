import { Badge } from "@/components/ui/Badge";
import type { Outcome } from "../types";

type Tone = "good" | "bad" | "neutral" | "warn" | "brand";

interface OutcomeMeta {
  emoji: string;
  label: string;
  color: string;
  tone: Tone;
}

export const OUTCOME_META: Record<Outcome, OutcomeMeta> = {
  caught: { emoji: "✅", label: "정확히 거부", color: "#137333", tone: "good" },
  correct_accept: { emoji: "⬜", label: "정확히 수용", color: "#5f6368", tone: "neutral" },
  missed: { emoji: "❌", label: "놓침", color: "#c5221f", tone: "bad" },
  false_alarm: { emoji: "⚠️", label: "오탐", color: "#b06000", tone: "warn" },
  bonus_found: { emoji: "💡", label: "추가 발견", color: "#1a73e8", tone: "brand" },
};

export function OutcomeBadge({ outcome }: { outcome: Outcome }) {
  const meta = OUTCOME_META[outcome];
  return (
    <Badge tone={meta.tone} role="status" aria-label={meta.label}>
      {meta.emoji} {meta.label}
    </Badge>
  );
}
