import type { Outcome } from "../types";

interface OutcomeMeta {
  emoji: string;
  label: string;
  color: string;
}

export const OUTCOME_META: Record<Outcome, OutcomeMeta> = {
  caught: { emoji: "✅", label: "정확히 거부", color: "#137333" },
  correct_accept: { emoji: "⬜", label: "정확히 수용", color: "#5f6368" },
  missed: { emoji: "❌", label: "놓침", color: "#c5221f" },
  false_alarm: { emoji: "⚠️", label: "오탐", color: "#b06000" },
  bonus_found: { emoji: "💡", label: "추가 발견", color: "#1a73e8" },
};

export function OutcomeBadge({ outcome }: { outcome: Outcome }) {
  const meta = OUTCOME_META[outcome];
  return (
    <span
      role="status"
      aria-label={meta.label}
      style={{ color: meta.color, fontWeight: 600 }}
    >
      {meta.emoji} {meta.label}
    </span>
  );
}
