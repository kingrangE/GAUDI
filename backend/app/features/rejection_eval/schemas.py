"""Pydantic schemas: LLM structured outputs + API request/response models."""

from typing import Literal

from pydantic import BaseModel, Field

FlawType = Literal["wrong_tech", "wrong_direction", "none"]
# Why an item must be rejected: an injected wrong design, or a decision not in
# the functional requirements (out of scope), or not a flaw at all.
FlawSource = Literal["injected", "out_of_scope", "none"]
Outcome = Literal["caught", "missed", "false_alarm", "correct_accept"]


# --- LLM structured outputs --------------------------------------------------
class GeneratedItem(BaseModel):
    """One design decision the AI 'chose' from the candidate's prompt.

    `is_flawed` marks an intentionally injected wrong design; it is independent
    of whether the decision is in the requirements (judged separately).
    """

    id: str
    text: str
    is_flawed: bool
    flaw_type: FlawType
    explanation: str


class GenerationOutput(BaseModel):
    items: list[GeneratedItem]


class ItemJudgement(BaseModel):
    """Judge's grounding call for one item against the requirements spec."""

    item_id: str
    in_requirements: bool


class JudgeOutput(BaseModel):
    """Per-item grounding (is the decision called for by the requirements?) plus
    a 1-2 line report. Items judged `in_requirements=false` are out-of-scope flaws."""

    report: str
    judgements: list[ItemJudgement] = Field(default_factory=list)


class PairwiseVerdict(BaseModel):
    """Head-to-head judgement: which of two candidates better rejected the wrong
    / out-of-scope design items. Used by the offline judge-reliability harness
    (position-bias), not by the app request path."""

    winner: Literal["A", "B", "tie"]
    reason: str


# --- API: create session -----------------------------------------------------
class CreateSessionRequest(BaseModel):
    # Optional: sessions are anonymous; identity is handled by the entry gate.
    candidate_name: str | None = None


class TopicMeta(BaseModel):
    index: int
    title: str
    description: str
    requirements: list[str]


class CreateSessionResponse(BaseModel):
    session_id: str
    candidate_name: str
    topics: list[TopicMeta]


# --- API: generate / submit --------------------------------------------------
class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)


class PublicItem(BaseModel):
    """An item shown to the candidate — ground-truth flags are hidden."""

    id: str
    text: str


class GenerateResponse(BaseModel):
    topic_index: int
    items: list[PublicItem]


class SubmitRequest(BaseModel):
    flagged_ids: list[str] = Field(default_factory=list)
    reasons: dict[str, str] = Field(default_factory=dict)


class SubmitResponse(BaseModel):
    topic_index: int
    submitted: bool


# --- API: result -------------------------------------------------------------
class ResultItem(BaseModel):
    id: str
    text: str
    is_flawed: bool
    flaw_type: FlawType
    in_requirements: bool
    flaw_source: FlawSource
    explanation: str
    flagged: bool
    outcome: Outcome


class ResultTopic(BaseModel):
    topic_index: int
    topic_title: str
    prompt: str
    items: list[ResultItem]
    precision: float
    recall: float
    f1: float
    report: str


class ResultResponse(BaseModel):
    session_id: str
    candidate_name: str
    status: str
    precision: float
    recall: float
    f1: float
    topics: list[ResultTopic]
