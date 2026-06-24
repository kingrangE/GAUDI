// Pure presentation logic for spec-design results (no React, so it is unit-testable).

import type {
  DimensionResult,
  EvaluationResult,
  Grade,
  Quality,
  RequirementResult,
} from "./types";

export type Tone = "great" | "good" | "warn" | "bad";

export interface Meta {
  label: string;
  tone: Tone;
}

const GRADE_META: Record<Grade, Meta> = {
  excellent: { label: "매우 우수", tone: "great" },
  good: { label: "우수", tone: "good" },
  fair: { label: "보통", tone: "warn" },
  poor: { label: "미흡", tone: "bad" },
};

const QUALITY_META: Record<Quality, Meta> = {
  good: { label: "좋음", tone: "great" },
  ok: { label: "무난", tone: "good" },
  weak: { label: "취약", tone: "warn" },
  bad: { label: "위험", tone: "bad" },
  unspecified: { label: "미지정", tone: "warn" },
  unknown: { label: "불명", tone: "warn" },
};

export function gradeMeta(grade: Grade | string): Meta {
  return GRADE_META[grade as Grade] ?? { label: "알 수 없음", tone: "warn" };
}

export function qualityMeta(quality: Quality | string): Meta {
  return QUALITY_META[quality as Quality] ?? { label: "불명", tone: "warn" };
}

/** 0..1 -> "73%" */
export function percent(ratio: number): string {
  return `${Math.round(ratio * 100)}%`;
}

/** Tone for one decision row: diverged (didn't pin) is amber; else by decision quality. */
export function dimensionTone(dim: DimensionResult): Tone {
  return dim.diverged ? "warn" : qualityMeta(dim.quality).tone;
}

/** Status label: "갈림" if not pinned, else the quality grade. */
export function dimensionStatus(dim: DimensionResult): string {
  return dim.diverged ? "갈림" : qualityMeta(dim.quality).label;
}

/** Decisions worst-score first, so problems surface at the top. */
export function dimensionsByScore(dims: DimensionResult[]): DimensionResult[] {
  return [...dims].sort((a, b) => a.score - b.score);
}

/** Requirements least-satisfied first. */
export function requirementsBySatisfaction(reqs: RequirementResult[]): RequirementResult[] {
  return [...reqs].sort((a, b) => a.satisfaction - b.satisfaction);
}

/** One-line headline summarizing the run. */
export function headline(result: EvaluationResult): string {
  const { score, requirements } = result;
  const failed = requirements.filter((r) => !r.satisfied).length;
  const grade = gradeMeta(score.grade).label;
  if (failed === 0 && score.weak_decisions.length === 0 && score.diverged_decisions.length === 0) {
    return `요구사항을 모두 충족하고 결정도 견고합니다 (${grade}).`;
  }
  if (failed > 0) {
    return `요구사항 ${requirements.length}개 중 ${failed}개 미충족 (${grade}).`;
  }
  return `보완·미지정 결정이 남아 있습니다 (${grade}).`;
}
