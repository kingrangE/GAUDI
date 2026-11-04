"""FastAPI router for dev-prompting evaluation. Mounted by the app during assembly.

The solver client is a dependency so tests can override it with a fake (LLM mocked).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from feature_demo.models import DemoSession
from feature_demo.routing import DemoRoute
from feature_demo.session import bind_resource, current_demo_session
from feature_dev_prompting import sessions
from feature_dev_prompting.evaluator import evaluate
from feature_dev_prompting.models import EvaluationResult, ProblemPublic
from feature_dev_prompting.problems import get_problem, list_problems
from llm.client import LLMClient, get_llm_client

router = APIRouter(route_class=DemoRoute, prefix="/dev-prompting", tags=["dev-prompting"])


def get_solver_client() -> LLMClient:
    """Injectable solver client (overridden in tests)."""

    return get_llm_client()


class EvaluateRequest(BaseModel):
    problem_id: str
    prompts: list[str]


@router.get("/problems", response_model=list[ProblemPublic])
def list_problems_endpoint() -> list[ProblemPublic]:
    return [ProblemPublic.from_problem(p) for p in list_problems()]


@router.get("/problems/{problem_id}", response_model=ProblemPublic)
def get_problem_endpoint(problem_id: str) -> ProblemPublic:
    problem = get_problem(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="unknown problem_id")
    return ProblemPublic.from_problem(problem)


@router.post("/evaluate", response_model=EvaluationResult)
def evaluate_endpoint(
    req: EvaluateRequest,
    client: LLMClient = Depends(get_solver_client),
) -> EvaluationResult:
    problem = get_problem(req.problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="unknown problem_id")
    if not req.prompts:
        raise HTTPException(status_code=422, detail="prompts must not be empty")
    return evaluate(problem, req.prompts, client=client)


class CreateRunRequest(BaseModel):
    problem_id: str


class TurnRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)
    turn: int = Field(ge=1, le=20)


@router.post("/runs")
async def create_run(
    req: CreateRunRequest, db: AsyncSession = Depends(get_session),
    visitor: DemoSession | None = Depends(current_demo_session),
) -> dict:
    if get_problem(req.problem_id) is None:
        raise HTTPException(status_code=404, detail="unknown problem_id")
    run = sessions.DevRun(problem_id=req.problem_id)
    db.add(run)
    await db.flush()
    bind_resource(db, visitor.id if visitor else None, "dev_prompting", run.id)
    await db.commit()
    await db.refresh(run)
    return sessions.result(run)


@router.post("/runs/{run_id}/turns")
async def next_turn(
    run_id: str,
    req: TurnRequest,
    db: AsyncSession = Depends(get_session),
    client: LLMClient = Depends(get_solver_client),
) -> dict:
    run = await db.get(sessions.DevRun, run_id)
    if run is None or run.exam_attempt_id is not None:
        raise HTTPException(status_code=404, detail="practice run not found")
    await sessions.run_turn(db, run, req.prompt, req.turn, client)
    return sessions.result(run)
