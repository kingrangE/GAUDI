"""Pydantic schemas: API request/response models for the CS deep evaluation.

The reference answer and rubric are deliberately absent from every
candidate-facing response — `/questions` exposes only the prompt.
"""

from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["grading", "graded", "failed"]
ResponseType = Literal["correct", "partial", "honest_unknown", "bluff_wrong"]


# --- questions ---------------------------------------------------------------
class QuestionPublic(BaseModel):
    id: str
    domain: str
    prompt_md: str
    ordinal: int


# --- submit / poll -----------------------------------------------------------
class AnswerInput(BaseModel):
    question_id: str = Field(min_length=1)
    # Empty is allowed — a blank answer is a valid (honest) "I don't know".
    answer_text: str = ""


class CreateSessionRequest(BaseModel):
    candidate_id: str = Field(min_length=1)
    answers: list[AnswerInput] = Field(min_length=1)


class SessionCreated(BaseModel):
    session_id: str
    status: Status


class AnswerResult(BaseModel):
    question_id: str
    domain: str
    response_type: ResponseType | None
    score: int | None
    matched_keywords: list[str] | None
    missing_keywords: list[str] | None
    rationale: str | None


class SessionResult(BaseModel):
    id: str
    candidate_id: str
    status: Status
    total_score: int | None
    normalized_score: int | None
    summary_report: str | None
    analysis_report: str | None
    per_question: list[AnswerResult]
    error: str | None
