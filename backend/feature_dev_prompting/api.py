"""FastAPI router for dev-prompting evaluation. Mounted by the app during assembly.

The solver client is a dependency so tests can override it with a fake (LLM mocked).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from feature_dev_prompting.evaluator import evaluate
from feature_dev_prompting.models import EvaluationResult, ProblemPublic
from feature_dev_prompting.problems import get_problem, list_problems
from llm.client import LLMClient, get_llm_client

router = APIRouter(prefix="/dev-prompting", tags=["dev-prompting"])


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
