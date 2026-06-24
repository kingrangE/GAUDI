"""FastAPI router for spec-design evaluation. Mounted by the app during assembly.

The generator and judge clients are dependencies so tests override them with fakes
(LLM mocked). Endpoints are async because evaluation fans out concurrent LLM calls.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from feature_spec_design.evaluator import evaluate
from feature_spec_design.models import EvaluationResult, TaskPublic
from feature_spec_design.tasks import get_task, list_tasks
from llm.client import LLMClient, get_gen_client, get_judge_client

router = APIRouter(prefix="/spec-design", tags=["spec-design"])


def get_gen_dependency() -> LLMClient:
    """Injectable generator client (overridden in tests)."""

    return get_gen_client()


def get_judge_dependency() -> LLMClient:
    """Injectable judge client (overridden in tests)."""

    return get_judge_client()


class EvaluateRequest(BaseModel):
    task_id: str
    instruction: str


@router.get("/tasks", response_model=list[TaskPublic])
def list_tasks_endpoint() -> list[TaskPublic]:
    return [TaskPublic.from_task(t) for t in list_tasks()]


@router.get("/tasks/{task_id}", response_model=TaskPublic)
def get_task_endpoint(task_id: str) -> TaskPublic:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="unknown task_id")
    return TaskPublic.from_task(task)


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_endpoint(
    req: EvaluateRequest,
    gen_client: LLMClient = Depends(get_gen_dependency),
    judge_client: LLMClient = Depends(get_judge_dependency),
) -> EvaluationResult:
    task = get_task(req.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="unknown task_id")
    if not req.instruction.strip():
        raise HTTPException(status_code=422, detail="instruction must not be empty")
    return await evaluate(task, req.instruction, gen_client=gen_client, judge_client=judge_client)
