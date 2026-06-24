"""Data models for the context-engineering evaluation (pydantic, FastAPI-friendly)."""

from __future__ import annotations

from pydantic import BaseModel


class FileNode(BaseModel):
    """One node of a sample project's file tree.

    Files carry their full `content` (served whole so the left panel can show it on click);
    directories carry `content=None`.
    """

    path: str  # POSIX relative path, e.g. "app/main.py"
    kind: str = "file"  # "file" | "dir"
    content: str | None = None


class Project(BaseModel):
    """A sample project the candidate inspects and writes a CLAUDE.md for."""

    id: str
    title: str
    brief: str  # short description shown alongside the tree
    files: list[FileNode]


class Submission(BaseModel):
    """A candidate's submitted CLAUDE.md for a given project."""

    project_id: str
    claude_md: str


class Criterion(BaseModel):
    """One ground-truth fact a good CLAUDE.md for a project must convey (answer-key item).

    Extracted from the project's gold reference (references.py); the judge checks coverage.
    """

    id: str
    text: str  # what the CLAUDE.md must convey (wording-independent)
    category: str = ""  # commands | structure | conventions | boundaries
    weight: float = 1.0


class CriterionVerdict(BaseModel):
    """Judge decision for one criterion against a candidate CLAUDE.md."""

    id: str
    covered: bool
    evidence: str = ""  # verbatim quote from the candidate doc; required when covered
    reason: str = ""


class ComponentScore(BaseModel):
    """One scorer's contribution to the total. Scoring is a SEPARATE track (SPEC §5)."""

    name: str
    score: float
    detail: str = ""


class EvaluationResult(BaseModel):
    """Submission outcome. `scores` stays empty until a ContextScorer is registered."""

    project_id: str
    claude_md: str
    scores: list[ComponentScore] = []
    total: float = 0.0


class CriterionResult(BaseModel):
    """One criterion's outcome for the UI: the criterion + whether the doc covered it."""

    id: str
    text: str
    category: str = ""
    covered: bool
    evidence: str = ""
    # Consensus confidence: share of judge runs backing this verdict (None = single run).
    agreement: float | None = None


class DimensionScore(BaseModel):
    """One scored axis of the benefit-driven composite (SPEC §5)."""

    key: str  # grounding | boundary | coverage | conciseness
    label: str
    score: float = 0.0  # 0–100
    weight: float = 0.0
    available: bool = True  # False when an LLM was required but absent
    detail: str = ""


class EvaluationReport(BaseModel):
    """Benefit-driven composite returned to the client on submission.

    `total` is the weighted mean over available dimensions; `results` is the per-criterion
    breakdown for the coverage dimension. Deterministic axes (grounding, conciseness) run even
    without an API key; coverage and boundary need the LLM and are marked unavailable otherwise.
    """

    project_id: str
    scored: bool = False
    total: float = 0.0  # weighted composite 0–100
    dimensions: list[DimensionScore] = []
    results: list[CriterionResult] = []
