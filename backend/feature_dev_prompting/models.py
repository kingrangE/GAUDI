"""Data models for the dev-prompting evaluation (pydantic, FastAPI-friendly).

Programmers-style: the candidate completes a function (`entry_point`); grading calls
that function with each case's `args` and compares the return value to `expected`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class GradingCase(BaseModel):
    """A single grading case: call `entry_point(*args)`, expect `expected` returned."""

    args: list[Any]
    expected: Any
    hidden: bool = False


class Problem(BaseModel):
    """An algorithm problem the candidate solves by completing a function via prompting."""

    id: str
    title: str
    statement: str
    constraints: str = ""
    entry_point: str = "solution"
    starter_code: str
    tests: list[GradingCase]
    time_limit_sec: float = 2.0


class CaseResult(BaseModel):
    """Outcome of running the generated function against one case.

    `expected`/`got` (JSON-rendered) are redacted (None) for hidden cases.
    """

    index: int
    hidden: bool
    passed: bool
    status: str  # pass | wrong_answer | runtime_error | timeout
    expected: str | None = None
    got: str | None = None


class TurnResult(BaseModel):
    """One prompt -> generated code -> graded run."""

    turn: int
    prompt: str
    code: str
    passed_count: int
    total: int
    solved: bool
    feedback: str
    case_results: list[CaseResult]


class ScoreBreakdown(BaseModel):
    """Final scoring: pass-rate component + understanding (turn-efficiency) component."""

    total: float
    pass_score: float
    understanding_score: float
    best_pass_rate: float
    solved: bool
    solved_turn: int | None = None


class EvaluationResult(BaseModel):
    """Full multi-turn evaluation outcome returned to the caller / API."""

    problem_id: str
    solved: bool
    score: ScoreBreakdown
    turns: list[TurnResult]


class Example(BaseModel):
    """A visible input/output example (a non-hidden grading case)."""

    args: list[Any]
    expected: Any


class ProblemPublic(BaseModel):
    """Client-safe view of a problem: never includes hidden test data."""

    id: str
    title: str
    statement: str
    constraints: str = ""
    entry_point: str
    starter_code: str
    time_limit_sec: float
    examples: list[Example]
    public_example_count: int

    @classmethod
    def from_problem(cls, problem: "Problem") -> "ProblemPublic":
        examples = [
            Example(args=t.args, expected=t.expected) for t in problem.tests if not t.hidden
        ]
        return cls(
            id=problem.id,
            title=problem.title,
            statement=problem.statement,
            constraints=problem.constraints,
            entry_point=problem.entry_point,
            starter_code=problem.starter_code,
            time_limit_sec=problem.time_limit_sec,
            examples=examples,
            public_example_count=len(examples),
        )
