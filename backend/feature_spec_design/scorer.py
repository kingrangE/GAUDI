"""Combine requirement coverage + decision (agreement × quality) into the final score.

Consistency alone is not rewarded: a decision only scores when it is both *pinned*
(high agreement) and *sound* (good quality), and a requirement only scores when the
generated solutions actually satisfy it. So a confidently-wrong or consistently-omitted
choice scores low, not high.

The blend weights consistency the highest (the spec-design axis is "답변 일관성"), with
requirement coverage and decision quality as correctness guards.
"""

from __future__ import annotations

from feature_spec_design.models import DimensionResult, RequirementResult, SpecScore

REQUIREMENT_WEIGHT = 0.3
DECISION_WEIGHT = 0.3
CONSISTENCY_WEIGHT = 0.4

GRADE_KO = {
    "good": "좋음",
    "ok": "무난",
    "weak": "취약",
    "bad": "위험",
    "unspecified": "미지정",
    "unknown": "불명",
}


def _grade(score: float) -> str:
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "good"
    if score >= 50:
        return "fair"
    return "poor"


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def score_spec(
    requirements: list[RequirementResult],
    dimensions: list[DimensionResult],
) -> SpecScore:
    requirement_score = round(100 * _mean([r.satisfaction for r in requirements]), 1)
    decision_score = round(100 * _mean([d.score for d in dimensions]), 1)
    consistency = round(100 * _mean([d.agreement for d in dimensions]), 1)
    total = round(
        REQUIREMENT_WEIGHT * requirement_score
        + DECISION_WEIGHT * decision_score
        + CONSISTENCY_WEIGHT * consistency,
        1,
    )
    grade = _grade(total)

    failed_requirements = [
        r.text for r in sorted(requirements, key=lambda r: r.satisfaction) if not r.satisfied
    ]
    weak_decisions = [
        f"{d.label}: {d.top_value} ({GRADE_KO.get(d.quality, d.quality)})"
        for d in dimensions
        if not d.diverged and d.quality_score < 0.7
    ]
    diverged_decisions = [
        d.label for d in sorted(dimensions, key=lambda d: d.agreement) if d.diverged
    ]

    return SpecScore(
        total=total,
        requirement_score=requirement_score,
        decision_score=decision_score,
        consistency=consistency,
        grade=grade,
        failed_requirements=failed_requirements,
        weak_decisions=weak_decisions,
        diverged_decisions=diverged_decisions,
        feedback=_feedback(failed_requirements, weak_decisions, diverged_decisions),
    )


def _feedback(failed: list[str], weak: list[str], diverged: list[str]) -> str:
    parts: list[str] = []
    if failed:
        parts.append(f"미충족 요구사항: {', '.join(failed)}.")
    if weak:
        parts.append(f"보완이 필요한 결정: {', '.join(weak)}.")
    if diverged:
        parts.append(f"명시하지 않아 실행마다 갈린 결정: {', '.join(diverged)}.")
    if not parts:
        return "요구사항을 모두 충족하고 설계 결정도 일관되고 견고합니다."
    return " ".join(parts)
