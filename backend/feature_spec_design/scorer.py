"""Combine requirement coverage + decision (agreement × quality) into the final score.

Consistency alone is not rewarded: a decision only scores when it is both *pinned*
(high agreement) and *sound* (good quality), and a requirement only scores when the
generated solutions actually satisfy it. So a confidently-wrong or consistently-omitted
choice scores low, not high.

The blend weights consistency the highest (the spec-design axis is "답변 일관성"), with
requirement coverage and decision quality as correctness guards. Finally, scope
discipline: features built consistently *beyond* the requirements (over-engineering)
subtract a capped penalty — good design also means not building what wasn't asked.
"""

from __future__ import annotations

from feature_spec_design.models import (
    DimensionResult,
    OverEngineeringItem,
    RequirementResult,
    SpecScore,
)

REQUIREMENT_WEIGHT = 0.3
DECISION_WEIGHT = 0.3
CONSISTENCY_WEIGHT = 0.4

OVERENGINEERING_PENALTY_PER_ITEM = 10.0
OVERENGINEERING_PENALTY_CAP = 30.0

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
    overengineering: list[OverEngineeringItem] | None = None,
) -> SpecScore:
    overengineering = overengineering or []
    requirement_score = round(100 * _mean([r.satisfaction for r in requirements]), 1)
    decision_score = round(100 * _mean([d.score for d in dimensions]), 1)
    consistency = round(100 * _mean([d.agreement for d in dimensions]), 1)
    base_score = round(
        REQUIREMENT_WEIGHT * requirement_score
        + DECISION_WEIGHT * decision_score
        + CONSISTENCY_WEIGHT * consistency,
        1,
    )

    penalty = min(
        OVERENGINEERING_PENALTY_CAP,
        OVERENGINEERING_PENALTY_PER_ITEM * len(overengineering),
    )
    total = round(max(0.0, base_score - penalty), 1)
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
    overengineered = [f"{it.label} ({round(it.prevalence * 100)}%)" for it in overengineering]

    return SpecScore(
        total=total,
        base_score=base_score,
        requirement_score=requirement_score,
        decision_score=decision_score,
        consistency=consistency,
        overengineering_penalty=round(penalty, 1),
        grade=grade,
        failed_requirements=failed_requirements,
        weak_decisions=weak_decisions,
        diverged_decisions=diverged_decisions,
        overengineered=overengineered,
        feedback=_feedback(failed_requirements, weak_decisions, diverged_decisions, overengineered),
    )


def _feedback(
    failed: list[str], weak: list[str], diverged: list[str], overengineered: list[str]
) -> str:
    parts: list[str] = []
    if failed:
        parts.append(f"미충족 요구사항: {', '.join(failed)}.")
    if weak:
        parts.append(f"보완이 필요한 결정: {', '.join(weak)}.")
    if diverged:
        parts.append(f"명시하지 않아 실행마다 갈린 결정: {', '.join(diverged)}.")
    if overengineered:
        parts.append(f"요구사항 밖 과설계(범위 축소 필요): {', '.join(overengineered)}.")
    if not parts:
        return "요구사항을 모두 충족하고, 결정도 견고하며, 불필요한 과설계도 없습니다."
    return " ".join(parts)
