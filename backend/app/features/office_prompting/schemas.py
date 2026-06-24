"""Pydantic schemas: LLM structured output + API request/response models.

The split between RunResponse (correctness HIDDEN during attempts) and
ResultResponse (correctness REVEALED after scoring) is deliberate — it keeps the
candidate from brute-forcing the answer across retries.
"""

from pydantic import BaseModel, Field


# --- LLM structured output ---------------------------------------------------
class ExtractionOutput(BaseModel):
    """What the LLM returns: just the ids satisfying the candidate's criteria."""

    ids: list[str] = Field(default_factory=list)


# --- API: create session -----------------------------------------------------
class CreateSessionRequest(BaseModel):
    candidate_name: str = Field(min_length=1)


class ProblemMeta(BaseModel):
    index: int
    title: str
    description: str  # human-facing; safe to show the candidate
    target_entity: str
    max_runs: int


class DatasetTable(BaseModel):
    name: str
    columns: list[str]
    rows: list[dict]


class CreateSessionResponse(BaseModel):
    session_id: str
    candidate_name: str
    problems: list[ProblemMeta]
    datasets: list[DatasetTable]  # full data — the candidate sees everything


# --- API: run (iteration; correctness HIDDEN) --------------------------------
class RunRequest(BaseModel):
    prompt: str = Field(min_length=1)


class RunResponse(BaseModel):
    problem_index: int
    run_number: int
    runs_used: int
    runs_remaining: int
    predicted_ids: list[str]
    predicted_rows: list[dict]  # rows for the returned ids — NO correctness flags


# --- API: result (correctness REVEALED) --------------------------------------
class ResultProblem(BaseModel):
    problem_index: int
    title: str
    target_entity: str
    final_prompt: str
    predicted_ids: list[str]
    truth_ids: list[str]
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    correct_count: int
    truth_count: int


class ResultResponse(BaseModel):
    session_id: str
    candidate_name: str
    status: str
    precision: float
    recall: float
    f1: float
    total_correct: int
    problems: list[ResultProblem]
