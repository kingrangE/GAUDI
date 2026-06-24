"""Candidate-facing mock-exam orchestration (`/api/mock-exam`).

A thin layer that chains the five mock-exam features into one themed
"실전 모의고사" (CX Churn-Radar) under a single overall timer, and **hides every
score from the candidate**: scoring happens server-side and each per-step result
is persisted through the existing `mock_exam.service` write contract (so the admin
console can read it), while the candidate only ever sees public material and a
`{recorded, next_step}` acknowledgement.

Design notes
------------
* **Single timer.** `remaining_seconds` is computed from `attempt.started_at`
  on every request — no schema change, no per-step clocks.
* **Score-hiding.** `submit` / `generate` / `get-step` / `finish` responses carry
  no score, grade, f1, precision, recall, weighted_score, or verdict. The native
  result blob (which *does* contain those) only ever goes into `record_feature_result`.
* **Per-feature adapters.** Each adapter maps the candidate's input to the
  feature's own scoring path and shapes a `raw_result` dict that contains the one
  field `normalize.py` requires for that feature. For `spec_design` and
  `dev_prompting` the headline score is copied up to a top-level ``"total"``
  (see the adapters for why, and the dev_prompting unit note).
* **rejection_eval** is generate-then-review and keeps its own session/attempt
  rows; we bind one rejection session per exam attempt by reusing the exam
  attempt id as the rejection session id (deterministic 1:1, no mapping table).
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.features.mock_exam.models import ExamAttempt, ExamFeatureResult
from app.features.mock_exam.service import (
    create_exam_attempt,
    finalize_exam_attempt,
    record_feature_result,
)

# rejection_eval
from app.features.rejection_eval import service as rej_service
from app.features.rejection_eval.models import RejectionAttempt, RejectionSession
from app.features.rejection_eval.schemas import SubmitRequest as RejSubmitRequest
from app.features.rejection_eval.topics import TOPICS

# test_design
from app.features.test_design import scoring as td_scoring
from app.features.test_design import services as td_services
from app.features.test_design.problems import find_problem as td_find_problem

# --- the five features (reused, never modified) ------------------------------
# context_engineering
from feature_context_engineering import (
    create_submission as ctx_create_submission,
)
from feature_context_engineering import (
    get_project as ctx_get_project,
)
from feature_context_engineering.evaluate import build_report as ctx_build_report

# dev_prompting
from feature_dev_prompting.api import get_solver_client
from feature_dev_prompting.evaluator import evaluate as dev_evaluate
from feature_dev_prompting.models import ProblemPublic as DevProblemPublic
from feature_dev_prompting.problems import get_problem as dev_get_problem

# spec_design
from feature_spec_design.evaluator import evaluate as spec_evaluate
from feature_spec_design.models import TaskPublic as SpecTaskPublic
from feature_spec_design.tasks import get_task as spec_get_task

# shared LLM config (for the context_engineering judge client)
from llm.client import LLMClient, get_llm_client
from llm.config import get_settings

# --------------------------------------------------------------------------- #
# Flow + theme content IDs
# --------------------------------------------------------------------------- #
EXAM_FLOW: list[str] = [
    "context_engineering",
    "spec_design",
    "rejection_eval",
    "test_design",
    "dev_prompting",
]
EXAM_TOTAL_SECONDS = 3600  # one overall 60-minute timer for the whole exam

# The themed "CX Churn-Radar" content each feature exposes (created by WP1–5).
CONTEXT_PROJECT_ID = "cx-churn-radar"
SPEC_TASK_ID = "cx-churn-radar-topn"
REJECTION_TOPIC_INDEX = 3
TEST_DESIGN_PROBLEM_ID = "cx-churn-radar"
DEV_PROBLEM_ID = "churn-risk-stream"


# --------------------------------------------------------------------------- #
# Request / response shapes (candidate-facing — never carry a score)
# --------------------------------------------------------------------------- #
class StartRequest(BaseModel):
    candidate_code: str


class StartResponse(BaseModel):
    attempt_id: str
    flow: list[str]
    current_step: str | None
    remaining_seconds: int


class AttemptStateResponse(BaseModel):
    flow: list[str]
    completed_steps: list[str]
    current_step: str | None
    remaining_seconds: int
    status: str


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)


class StepSubmitRequest(BaseModel):
    """Union of every step's input; each adapter validates its own field."""

    claude_md: str | None = None  # context_engineering
    instruction: str | None = None  # spec_design
    flagged_ids: list[str] | None = None  # rejection_eval
    reasons: dict[str, str] | None = None  # rejection_eval
    flaws: list[str] | None = None  # test_design
    prompts: list[str] | None = None  # dev_prompting


class SubmitResponse(BaseModel):
    recorded: bool
    next_step: str | None


class FinishResponse(BaseModel):
    completed: bool


# --------------------------------------------------------------------------- #
# Dependencies
# --------------------------------------------------------------------------- #
def get_context_client() -> LLMClient | None:
    """LLM client for the context_engineering coverage/boundary judges.

    Returns ``None`` when no API key is configured: ``build_report`` then scores
    only its deterministic axes (so the exam works keyless, and unit tests are
    hermetic). Exposed as a dependency so tests can force it via an override.
    """
    settings = get_settings()
    return get_llm_client(settings) if settings.api_key else None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _remaining_seconds(attempt: ExamAttempt) -> int:
    """Server-computed countdown from the single overall timer; clamps at 0."""
    started = attempt.started_at
    if started.tzinfo is None:  # SQLite may round-trip a naive datetime
        started = started.replace(tzinfo=timezone.utc)
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    return max(0, int(EXAM_TOTAL_SECONDS - elapsed))


async def _get_attempt_or_404(db: AsyncSession, attempt_id: str) -> ExamAttempt:
    attempt = await db.get(ExamAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="exam attempt not found")
    return attempt


async def _completed_steps(db: AsyncSession, attempt_id: str) -> list[str]:
    """Recorded feature_results for this attempt, in canonical EXAM_FLOW order."""
    rows = await db.scalars(
        select(ExamFeatureResult.feature_key).where(
            ExamFeatureResult.exam_attempt_id == attempt_id
        )
    )
    recorded = set(rows.all())
    return [f for f in EXAM_FLOW if f in recorded]


def _current_step(completed: list[str]) -> str | None:
    """First EXAM_FLOW step not yet completed, or None when the flow is done."""
    for feature_key in EXAM_FLOW:
        if feature_key not in completed:
            return feature_key
    return None


def _require(value, feature_key: str, field: str):
    if value is None or (isinstance(value, str) and not value.strip()):
        raise HTTPException(
            status_code=400, detail=f"{feature_key} requires {field!r}"
        )
    return value


# --------------------------------------------------------------------------- #
# Public material (theme content; NO answer key, NO score)
# --------------------------------------------------------------------------- #
def _public_material(feature_key: str) -> dict:
    if feature_key == "context_engineering":
        project = ctx_get_project(CONTEXT_PROJECT_ID)
        if project is None:
            raise HTTPException(status_code=500, detail="context project missing")
        # Project = id/title/brief/files (the sample repo); rubric/gold/probe live
        # in separate modules the candidate never sees.
        return project.model_dump()

    if feature_key == "spec_design":
        task = spec_get_task(SPEC_TASK_ID)
        if task is None:
            raise HTTPException(status_code=500, detail="spec task missing")
        # TaskPublic = brief + counts only; the decision rubric is dropped.
        return SpecTaskPublic.from_task(task).model_dump()

    if feature_key == "rejection_eval":
        topic = TOPICS[REJECTION_TOPIC_INDEX]
        # Topic spec is public; injected flaws are only created at generate time.
        return {
            "topic_index": REJECTION_TOPIC_INDEX,
            "title": topic.title,
            "description": topic.description,
            "requirements": list(topic.requirements),
        }

    if feature_key == "test_design":
        pub = next(
            (p for p in td_services.public_problems() if p.id == TEST_DESIGN_PROBLEM_ID),
            None,
        )
        if pub is None:
            raise HTTPException(status_code=500, detail="test-design problem missing")
        # ProblemPublic = spec + provided_tests; the flaw catalog is absent.
        return pub.model_dump()

    if feature_key == "dev_prompting":
        problem = dev_get_problem(DEV_PROBLEM_ID)
        if problem is None:
            raise HTTPException(status_code=500, detail="dev-prompting problem missing")
        # ProblemPublic keeps only non-hidden examples; solution + hidden tests gone.
        return DevProblemPublic.from_problem(problem).model_dump()

    raise HTTPException(status_code=404, detail=f"unknown exam step: {feature_key}")


# --------------------------------------------------------------------------- #
# rejection_eval session bridge (one rejection session per exam attempt)
# --------------------------------------------------------------------------- #
async def _ensure_rejection_session(db: AsyncSession, attempt: ExamAttempt) -> None:
    """Reuse the exam attempt id as the rejection session id (idempotent).

    Mirrors `rejection_eval.service.create_session` (one attempt row per topic)
    but with a deterministic id, so generate/submit for this exam attempt always
    resolve the same rejection session — no mapping table, no schema change.
    """
    if await db.get(RejectionSession, attempt.id) is not None:
        return
    session = RejectionSession(
        id=attempt.id,
        candidate_name=attempt.candidate_label,
        user_id=attempt.candidate_code,
        status="in_progress",
    )
    db.add(session)
    await db.flush()
    for index, topic in enumerate(TOPICS):
        db.add(
            RejectionAttempt(
                session_id=session.id, topic_index=index, topic_title=topic.title
            )
        )
    await db.commit()


# --------------------------------------------------------------------------- #
# Per-feature scoring adapters → raw_result dict (with the normalize field)
# --------------------------------------------------------------------------- #
def _score_context(claude_md: str | None, client: LLMClient | None) -> dict:
    _require(claude_md, "context_engineering", "claude_md")
    project = ctx_get_project(CONTEXT_PROJECT_ID)
    if project is None:
        raise HTTPException(status_code=500, detail="context project missing")
    try:
        submission = ctx_create_submission(CONTEXT_PROJECT_ID, claude_md)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    report = ctx_build_report(project, submission, client)
    # EvaluationReport.total is already 0–100 -> normalize uses scale 1.0.
    return report.model_dump()


async def _score_spec(instruction: str | None) -> dict:
    _require(instruction, "spec_design", "instruction")
    task = spec_get_task(SPEC_TASK_ID)
    if task is None:
        raise HTTPException(status_code=500, detail="spec task missing")
    result = await spec_evaluate(task, instruction)
    raw = result.model_dump()
    # model_dump exposes score.total / total_score but NOT a top-level "total";
    # normalize.py reads raw["total"] (scale 1.0, already 0–100) -> copy it up.
    raw["total"] = result.score.total
    return raw


async def _score_rejection(
    db: AsyncSession, attempt: ExamAttempt, body: StepSubmitRequest
) -> dict:
    await _ensure_rejection_session(db, attempt)
    req = RejSubmitRequest(
        flagged_ids=body.flagged_ids or [],
        reasons=body.reasons or {},
    )
    # 409 if the candidate never called generate first (no items to review).
    await rej_service.submit_for_topic(db, attempt.id, REJECTION_TOPIC_INDEX, req)
    result = await rej_service.score_session(db, attempt.id)
    # ResultResponse has a top-level "f1" (0–1) -> normalize uses scale 100.
    return result.model_dump()


async def _score_test_design(flaws: list[str] | None) -> dict:
    if flaws is None:
        raise HTTPException(status_code=400, detail="test_design requires 'flaws'")
    problem = td_find_problem(TEST_DESIGN_PROBLEM_ID)
    if problem is None:
        raise HTTPException(status_code=500, detail="test-design problem missing")
    # Call via the services module so the judge seam stays patchable in tests.
    judged = await td_services.judge_submission(problem, flaws)
    gt_flaws = [asdict(f) for f in problem.flaws]
    matches = [m.model_dump() for m in judged.matches]
    # score_submission returns a dict with a top-level "weighted_score" (0–1).
    return td_scoring.score_submission(
        gt_flaws,
        flaws,
        matches,
        report=judged.report,
        already_covered_indices=judged.already_covered_indices,
    )


def _score_dev_prompting(prompts: list[str] | None, solver: LLMClient) -> dict:
    if not prompts:
        raise HTTPException(status_code=400, detail="dev_prompting requires 'prompts'")
    problem = dev_get_problem(DEV_PROBLEM_ID)
    if problem is None:
        raise HTTPException(status_code=500, detail="dev-prompting problem missing")
    result = dev_evaluate(problem, prompts, client=solver)
    raw = result.model_dump()
    # ScoreBreakdown.total is 0–100, but normalize.py multiplies dev_prompting's
    # "total" by 100 (it expects a 0–1 value). Scale to 0–1 here so the persisted
    # normalized score is the true 0–100 composite (not saturated at 100).
    raw["total"] = result.score.total / 100.0
    return raw


async def _score_step(
    feature_key: str,
    db: AsyncSession,
    attempt: ExamAttempt,
    body: StepSubmitRequest,
    solver: LLMClient,
    context_client: LLMClient | None,
) -> dict:
    if feature_key == "context_engineering":
        return _score_context(body.claude_md, context_client)
    if feature_key == "spec_design":
        return await _score_spec(body.instruction)
    if feature_key == "rejection_eval":
        return await _score_rejection(db, attempt, body)
    if feature_key == "test_design":
        return await _score_test_design(body.flaws)
    if feature_key == "dev_prompting":
        return _score_dev_prompting(body.prompts, solver)
    raise HTTPException(status_code=404, detail=f"unknown exam step: {feature_key}")


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
router = APIRouter(prefix="/api/mock-exam", tags=["mock-exam"])


@router.post("/start", response_model=StartResponse)
async def start(
    body: StartRequest, db: AsyncSession = Depends(get_session)
) -> StartResponse:
    try:
        attempt = await create_exam_attempt(db, body.candidate_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StartResponse(
        attempt_id=attempt.id,
        flow=EXAM_FLOW,
        current_step=EXAM_FLOW[0],
        remaining_seconds=_remaining_seconds(attempt),
    )


@router.get("/attempts/{attempt_id}", response_model=AttemptStateResponse)
async def get_attempt(
    attempt_id: str, db: AsyncSession = Depends(get_session)
) -> AttemptStateResponse:
    attempt = await _get_attempt_or_404(db, attempt_id)
    completed = await _completed_steps(db, attempt.id)
    return AttemptStateResponse(
        flow=EXAM_FLOW,
        completed_steps=completed,
        current_step=_current_step(completed),
        remaining_seconds=_remaining_seconds(attempt),
        status=attempt.status,
    )


@router.get("/attempts/{attempt_id}/steps/{feature_key}")
async def get_step(
    attempt_id: str, feature_key: str, db: AsyncSession = Depends(get_session)
) -> dict:
    await _get_attempt_or_404(db, attempt_id)
    if feature_key not in EXAM_FLOW:
        raise HTTPException(status_code=404, detail=f"unknown exam step: {feature_key}")
    return {"feature_key": feature_key, "material": _public_material(feature_key)}


@router.post("/attempts/{attempt_id}/steps/rejection_eval/generate")
async def generate_rejection_items(
    attempt_id: str,
    body: GenerateRequest,
    db: AsyncSession = Depends(get_session),
) -> dict:
    attempt = await _get_attempt_or_404(db, attempt_id)
    await _ensure_rejection_session(db, attempt)
    resp = await rej_service.generate_for_topic(
        db, attempt.id, REJECTION_TOPIC_INDEX, body.prompt
    )
    # PublicItem = {id, text} only — is_flawed / explanation stay server-side.
    return {
        "feature_key": "rejection_eval",
        "items": [item.model_dump() for item in resp.items],
    }


@router.post("/attempts/{attempt_id}/steps/{feature_key}/submit", response_model=SubmitResponse)
async def submit_step(
    attempt_id: str,
    feature_key: str,
    body: StepSubmitRequest,
    db: AsyncSession = Depends(get_session),
    solver: LLMClient = Depends(get_solver_client),
    context_client: LLMClient | None = Depends(get_context_client),
) -> SubmitResponse:
    attempt = await _get_attempt_or_404(db, attempt_id)
    if feature_key not in EXAM_FLOW:
        raise HTTPException(status_code=404, detail=f"unknown exam step: {feature_key}")

    # Score server-side, then persist via the existing write contract. The native
    # result (which carries the score) never reaches the candidate.
    raw_result = await _score_step(feature_key, db, attempt, body, solver, context_client)
    await record_feature_result(db, attempt.id, feature_key, raw_result)

    completed = await _completed_steps(db, attempt.id)
    return SubmitResponse(recorded=True, next_step=_current_step(completed))


@router.post("/attempts/{attempt_id}/finish", response_model=FinishResponse)
async def finish(
    attempt_id: str, db: AsyncSession = Depends(get_session)
) -> FinishResponse:
    # Allowed even when remaining_seconds == 0 — finalize averages whatever was
    # recorded (a partial exam still produces a partial average).
    await _get_attempt_or_404(db, attempt_id)
    await finalize_exam_attempt(db, attempt_id)
    return FinishResponse(completed=True)
