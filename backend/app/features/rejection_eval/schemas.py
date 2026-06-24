"""Pydantic schemas: LLM structured outputs + API request/response models."""

from typing import Literal

from pydantic import BaseModel, Field

FlawType = Literal["wrong_tech", "wrong_direction", "none"]
Outcome = Literal["caught", "missed", "false_alarm", "correct_accept", "bonus_found"]


# --- LLM structured outputs --------------------------------------------------
class GeneratedItem(BaseModel):
    """One design decision the AI 'chose', possibly an intentional flaw."""

    id: str
    text: str
    is_flawed: bool
    flaw_type: FlawType
    explanation: str


class GenerationOutput(BaseModel):
    items: list[GeneratedItem]


class JudgeOutput(BaseModel):
    """Judge reconciliation: a 1-2 line report and any candidate-flagged items
    that are genuinely real flaws even though the generator didn't intend them."""

    report: str
    bonus_item_ids: list[str] = Field(default_factory=list)


# --- API: create session -----------------------------------------------------
class CreateSessionRequest(BaseModel):
    candidate_name: str = Field(min_length=1)


class TopicMeta(BaseModel):
    index: int
    title: str
    description: str


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
