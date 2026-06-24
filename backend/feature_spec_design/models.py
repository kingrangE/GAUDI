"""Data models for spec-design evaluation (pydantic, FastAPI-friendly).

The score combines three axes, all grounded in an explicit per-task spec (so it measures
quality, not just self-consistency):
- **Requirement coverage** — do the generated solutions actually satisfy the task's
  functional requirements (across the N runs)?
- **Decision quality × consistency** — for each design decision, did the instruction pin
  a *sound* choice? Scored as agreement × quality(modal value), so a confidently-wrong or
  consistently-omitted decision scores low instead of high.
- Consistency (mean agreement) is reported as context.
"""

from __future__ import annotations

from pydantic import BaseModel

# Quality grades a design decision option can carry, and their numeric weight.
QUALITY_SCORES: dict[str, float] = {"good": 1.0, "ok": 0.7, "weak": 0.4, "bad": 0.0}
UNSPECIFIED = "unspecified"


class DimensionOption(BaseModel):
    """A known value for a decision dimension, with a quality grade."""

    value: str  # canonical lowercase label, e.g. "bcrypt"
    quality: str  # good | ok | weak | bad


class DecisionDimension(BaseModel):
    """One design decision we score (hidden rubric — never shown to the candidate)."""

    key: str
    label: str
    description: str
    options: list[DimensionOption]


class Requirement(BaseModel):
    """A checkable functional requirement (shown to the candidate in the brief)."""

    id: str
    text: str


class SpecTask(BaseModel):
    """A development brief: candidate-facing requirements + a hidden decision rubric."""

    id: str
    title: str
    brief: str
    requirements: list[Requirement]
    dimensions: list[DecisionDimension]


class TaskPublic(BaseModel):
    """Client-safe view: brief + counts only (never the decision rubric)."""

    id: str
    title: str
    brief: str
    requirement_count: int
    dimension_count: int

    @classmethod
    def from_task(cls, task: "SpecTask") -> "TaskPublic":
        return cls(
            id=task.id,
            title=task.title,
            brief=task.brief,
            requirement_count=len(task.requirements),
            dimension_count=len(task.dimensions),
        )


class Sample(BaseModel):
    """One generated design/implementation for the candidate's instruction."""

    index: int
    content: str


class SampleJudgement(BaseModel):
    """The judge's read of one sample: which requirements it meets + its decisions."""

    index: int
    requirements_met: list[str]  # requirement ids
    decisions: dict[str, str]  # dimension key -> chosen value label


class RequirementResult(BaseModel):
    """How reliably the N samples satisfied one requirement."""

    id: str
    text: str
    met_count: int
    total: int
    satisfaction: float  # met_count / total
    satisfied: bool  # satisfaction >= threshold


class DimensionResult(BaseModel):
    """Per-decision outcome: consistency × quality of the modal choice."""

    key: str
    label: str
    distribution: dict[str, int]
    top_value: str
    agreement: float  # share of samples on the modal value
    quality: str  # grade of the modal value (good|ok|weak|bad|unspecified)
    quality_score: float  # numeric quality of the modal value
    score: float  # agreement × quality_score
    diverged: bool  # agreement below threshold (instruction didn't pin it)


class SpecScore(BaseModel):
    """Final score (0..100) and its three-axis breakdown + actionable feedback."""

    total: float
    requirement_score: float  # 0..100
    decision_score: float  # 0..100
    consistency: float  # 0..100 (mean agreement, reported)
    grade: str  # excellent | good | fair | poor
    failed_requirements: list[str]  # texts of under-met requirements
    weak_decisions: list[str]  # "비밀번호 저장: md5 (취약)"
    diverged_decisions: list[str]  # labels of decisions the instruction left open
    feedback: str


class EvaluationResult(BaseModel):
    """Full spec-design evaluation outcome returned to the caller / API."""

    task_id: str
    instruction: str
    total_score: float
    score: SpecScore
    requirements: list[RequirementResult]
    dimensions: list[DimensionResult]
    samples: list[Sample]
