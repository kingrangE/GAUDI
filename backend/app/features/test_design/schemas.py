"""Pydantic schemas: LLM structured outputs + API request/response models."""

from typing import Literal

from pydantic import BaseModel, Field


# --- LLM structured output ---------------------------------------------------
class JudgeMatch(BaseModel):
    """The judge's verdict for one ground-truth flaw."""

    ground_truth_id: str
    matched: bool
    # index into the candidate's submitted flaw list that matched this flaw,
    # or null if the candidate did not find it.
    candidate_index: int | None
    # 0-2 quality of the candidate's description (only meaningful when matched):
    # 0 = symptom only / vague, 1 = correct gist, 2 = root cause + condition.
    quality: int


class JudgeOutput(BaseModel):
    """Semantic matching of a candidate's free-text flaws to the ground truth."""

    matches: list[JudgeMatch]
    # indices of submitted flaws that match no real flaw (hallucinated / wrong).
    false_positive_indices: list[int] = Field(default_factory=list)
    # indices of submitted items that merely restate a provided basic test —
    # neither a match nor a false positive (scored neutrally).
    already_covered_indices: list[int] = Field(default_factory=list)
    report: str


class PairwiseVerdict(BaseModel):
    """Which of two submissions is stronger (offline position-bias harness)."""

    winner: Literal["A", "B", "tie"]
    reason: str


# --- API: create session -----------------------------------------------------
class CreateSessionRequest(BaseModel):
    candidate_name: str = Field(min_length=1)


class ProblemPublic(BaseModel):
    """A problem as shown to the candidate — the answer set is hidden.

    ``spec`` is the prose scenario (service + feature + tech + how it's built);
    there is no code to review. ``difficulty`` is one of easy/medium/hard.
    """

    index: int
    id: str
    title: str
    difficulty: str
    spec: str
    # Basic tests assumed already implemented — shown as a starting point.
    provided_tests: list[str]


class CreateSessionResponse(BaseModel):
    session_id: str
    candidate_name: str
    problems: list[ProblemPublic]


# --- API: submit -------------------------------------------------------------
class SubmitRequest(BaseModel):
    flaws: list[str] = Field(min_length=1)


class SubmitResponse(BaseModel):
    problem_index: int
    submitted: bool


# --- API: result -------------------------------------------------------------
class ResultFlaw(BaseModel):
    """One ground-truth flaw, revealed with whether the candidate found it."""

    id: str
    text: str
    severity: str
    category: str
    found: bool
    quality: int
    matched_candidate_text: str | None


class ResultProblem(BaseModel):
    problem_index: int
    problem_id: str
    title: str
    difficulty: str
    provided_tests: list[str]
    candidate_flaws: list[str]
    flaws: list[ResultFlaw]
    false_positives: list[str]
    recall: float
    precision: float
    mean_quality: float
    weighted_score: float
    report: str


class ResultResponse(BaseModel):
    session_id: str
    candidate_name: str
    status: str
    recall: float
    precision: float
    weighted_score: float
    problems: list[ResultProblem]
