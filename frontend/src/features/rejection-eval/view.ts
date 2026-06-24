// Pure presentation logic for rejection-eval results (no React, unit-testable).

import type { FlawSource, Outcome } from "./types";

export type Tone = "good" | "warn" | "bad" | "neutral";

export interface Meta {
  label: string;
  tone: Tone;
}

/** 0..1 -> "73%" */
export function percent(ratio: number): string {
  return `${Math.round(ratio * 100)}%`;
}

/** Overall verdict from F1 (the headline metric). */
export function verdictMeta(f1: number): Meta {
  if (f1 >= 0.8) return { label: "우수", tone: "good" };
  if (f1 >= 0.5) return { label: "보통", tone: "warn" };
  return { label: "미흡", tone: "bad" };
}

/** Per-item outcome -> label + tone. */
export function outcomeMeta(outcome: Outcome): Meta {
  switch (outcome) {
    case "caught":
      return { label: "정확히 거부", tone: "good" };
    case "missed":
      return { label: "놓침", tone: "bad" };
    case "false_alarm":
      return { label: "오탐", tone: "warn" };
    case "correct_accept":
      return { label: "정확히 수용", tone: "neutral" };
    case "bonus_found":
      return { label: "추가 발견", tone: "good" };
    default:
      return { label: "—", tone: "neutral" };
  }
}

/** Why an item had to be rejected (empty for non-flaws). */
export function flawSourceLabel(source: FlawSource): string {
  switch (source) {
    case "injected":
      return "잘못된 설계";
    case "out_of_scope":
      return "요구사항에 없음";
    default:
      return "";
  }
}

/** Whether the candidate should have rejected this item. */
export function shouldReject(source: FlawSource): boolean {
  return source !== "none";
}

/** The candidate's own action label. */
export function decisionLabel(flagged: boolean): string {
  return flagged ? "거부" : "수용";
}
