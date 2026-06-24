"""Pydantic schemas: API request/response models for the coding test.

The grading-case inputs, reference solution, and rubric are deliberately
absent from every candidate-facing response — only sample cases are exposed.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

Status = Literal["grading", "graded", "failed"]


# --- problems ----------------------------------------------------------------
class ProblemSummary(BaseModel):
    id: str
    title: str
    difficulty: str


class SampleCase(BaseModel):
    """A visible sample case — args + expected return are shown to the candidate."""

    args: list[Any]
    expected: Any


class ProblemDetail(BaseModel):
    id: str
    title: str
    description_md: str
    function_name: str
    starter_code: str
    difficulty: str
    sample_cases: list[SampleCase]


# --- run (sample execution, not persisted) -----------------------------------
class RunRequest(BaseModel):
    code: str = Field(min_length=1)


class CaseRunResult(BaseModel):
    index: int
    passed: bool
    error: str | None = None


class RunResponse(BaseModel):
    results: list[CaseRunResult]


# --- submit / poll -----------------------------------------------------------
class CreateSubmissionRequest(BaseModel):
    problem_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    code: str = Field(min_length=1)


class SubmissionCreated(BaseModel):
    submission_id: str
    status: Status


class SubmissionResult(BaseModel):
    id: str
    problem_id: str
    candidate_id: str
    status: Status
    test_passed: int | None
    test_total: int | None
    strengths: list[str] | None
    weaknesses: list[str] | None
    analysis_report: str | None
    code_quality_score: int | None
    error: str | None
